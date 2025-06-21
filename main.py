#!/usr/bin/env python
import asyncio
from typing import List

from crewai.flow.flow import Flow, listen, start
from pydantic import BaseModel

from write_a_book_with_flows.crews.write_book_chapter_crew.write_book_chapter_crew import (
    WriteBookChapterCrew,
)
from write_a_book_with_flows.types import Chapter, ChapterOutline

from write_a_book_with_flows.crews.outline_book_crew.outline_crew import OutlineCrew


class LivroEstado(BaseModel):
    id: str = "1"
    titulo: str = "A Lenda da Espada Encantada"
    livro: List[Chapter] = []
    esboco_livro: List[ChapterOutline] = []
    topico: str = (
        "Uma jornada épica em um reino mágico para encontrar uma espada lendária e derrotar um antigo mal."
    )
    objetivo: str = """
        O objetivo deste livro é transportar o leitor para um mundo de fantasia rico em detalhes,
        com personagens cativantes, magia ancestral e batalhas emocionantes. A narrativa deve
        explorar temas de coragem, amizade e o eterno conflito entre o bem e o mal, culminando
        em um confronto final épico.
    """


class FluxoLivro(Flow[LivroEstado]):
    initial_state = LivroEstado

    @start()
    def gerar_esboco_livro(self):
        print("Iniciando a Equipe de Esboço do Livro")
        output = (
            OutlineCrew()
            .crew()
            .kickoff(inputs={"topic": self.state.topico, "goal": self.state.objetivo})
        )

        capitulos = output["chapters"]
        print("Capítulos:", capitulos)

        self.state.esboco_livro = capitulos
        return capitulos

    @listen(gerar_esboco_livro)
    async def escrever_capitulos(self):
        print("Escrevendo os Capítulos do Livro")
        tarefas = []

        async def escrever_capitulo_unico(esboco_capitulo):
            output = (
                WriteBookChapterCrew()
                .crew()
                .kickoff(
                    inputs={
                        "goal": self.state.objetivo,
                        "topic": self.state.topico,
                        "chapter_title": esboco_capitulo.title,
                        "chapter_description": esboco_capitulo.description,
                        "book_outline": [
                            esboco_capitulo.model_dump_json()
                            for esboco_capitulo in self.state.esboco_livro
                        ],
                    }
                )
            )
            titulo = output["title"]
            conteudo = output["content"]
            capitulo = Chapter(title=titulo, content=conteudo)
            return capitulo

        for esboco_capitulo in self.state.esboco_livro:
            print(f"Escrevendo Capítulo: {esboco_capitulo.title}")
            print(f"Descrição: {esboco_capitulo.description}")
            # Agendar cada tarefa de escrita de capítulo
            tarefa = asyncio.create_task(escrever_capitulo_unico(esboco_capitulo))
            tarefas.append(tarefa)

        # Aguardar todas as tarefas de escrita de capítulo concorrentemente
        capitulos = await asyncio.gather(*tarefas)
        print("Capítulos recém-gerados:", capitulos)
        self.state.livro.extend(capitulos)

        print("Capítulos do Livro", self.state.livro)

    @listen(escrever_capitulos)
    async def juntar_e_salvar_capitulo(self):
        print("Juntando e Salvando os Capítulos do Livro")
        # Combinar todos os capítulos em uma única string markdown
        conteudo_livro = ""

        for capitulo in self.state.livro:
            # Adicionar o título do capítulo como um cabeçalho H1
            conteudo_livro += f"# {capitulo.title}\n\n"
            # Adicionar o conteúdo do capítulo
            conteudo_livro += f"{capitulo.content}\n\n"

        # O título do livro de self.state.titulo
        titulo_livro = self.state.titulo

        # Criar o nome do arquivo substituindo espaços por underscores e adicionando a extensão .md
        nome_arquivo = f"./{titulo_livro.replace(' ', '_')}.md"

        # Salvar o conteúdo combinado no arquivo
        with open(nome_arquivo, "w", encoding="utf-8") as file:
            file.write(conteudo_livro)

        print(f"Livro salvo como {nome_arquivo}")
        return conteudo_livro


def iniciar():
    fluxo_livro = FluxoLivro()
    fluxo_livro.kickoff()


def plotar():
    fluxo_livro = FluxoLivro()
    fluxo_livro.plot()


if __name__ == "__main__":
    iniciar()
