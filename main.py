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
    titulo: str = "Paulo: O Despertar do Filho da Magia"
    livro: List[Chapter] = []
    esboco_livro: List[ChapterOutline] = []
    topico: str = (
        "Paulo, um rapaz de 20 anos, nascido em São Paulo e deficiente visual desde o nascimento, vive com sua mãe, Margarida, "
        "que é empregada doméstica na casa da família Montenegro. Apesar da compreensão e ajuda dos patrões de sua mãe, Paulo enfrenta o desprezo de Juliana, "
        "a filha do casal, dois anos mais nova. Margarida se entristece com o tratamento dado a Paulo. Paulo sempre teve sonhos vívidos com magos, fadas, "
        "duendes e gnomos, sobre os quais sua mãe evita falar. O pai de Paulo desapareceu misteriosamente antes de seu nascimento. "
        "Em uma noite, um ser de pura luz aparece em seu sonho, revelando: 'Em breve, filho da magia, você despertará'."
    )
    objetivo: str = """
        Este livro narrará a jornada de Paulo, desde sua vida cotidiana e os desafios de sua deficiência visual, até o despertar de seus poderes mágicos latentes.
        A história explorará o desenvolvimento de suas habilidades, a mudança em sua relação com Juliana após eventos impactantes (como salvá-la de um perigo iminente,
        revelando seus poderes), e a busca pela verdade sobre o desaparecimento de seu pai e sua conexão com o mundo da magia.
        A trama envolverá profecias antigas ('Em breve, o filho da magia irá despertar. fiquem de olho'), confrontos inesperados (Paulo usando seus poderes instintivamente para proteger Juliana:
        'Juliana! não! paulo entrou na frente dela quando o bandido atirou. Paulo instintivamente estendeu a mão e um raio atingiu o atirador, transformando-o em cinzas.'),
        reflexões e mudanças de perspectiva ('Paulo salvou a minha vida... porque, se eu sempre fui ruim com ele? o que está acontecendo?'),
        e possíveis manipulações ou segredos guardados ('...algumas memórias precisam ser alteradas - disse o estranho...').
        O objetivo é criar uma narrativa envolvente sobre autodescoberta, aceitação, o poder do inesperado e o desvendar de um destino mágico.
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
