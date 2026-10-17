# 📖 Guia de Comandos GSD (Get Shit Done)

> Este guia traduz e explica todos os comandos do ecossistema GSD em Português (pt-BR), incluindo exemplos práticos de casos de uso para você saber exatamente quando usar cada um.

---

## 🧭 O Fluxo Básico Recomendado (Como trabalhar no dia a dia)

Se você não sabe por onde começar, siga este ciclo padrão para cada nova funcionalidade/fase:

```text
/gsd-next  ➔  /gsd-discuss-phase  ➔  /gsd-plan-phase  ➔  /gsd-execute-phase  ➔  /gsd-verify-work
(Saber o que fazer)   (Alinhar detalhes)     (Criar plano de ação)      (Codificar/Construir)      (Testar e aprovar)
```

---

## 🚀 1. Principais do Dia a Dia (Workflow Central)

| Comando | Nome em Português | O que faz? | Exemplo de Caso de Uso |
| :--- | :--- | :--- | :--- |
| **`/gsd-next`** | Próximo Passo | Analisa o estado atual do projeto e indica/inicia o próximo passo recomendado. | *Você abriu o projeto hoje e quer saber qual é a próxima tarefa a ser feita.* |
| **`/gsd-progress`** | Ver Progresso | Mostra o resumo geral de status: fases concluídas, fase atual e o que resta fazer. | *Quer ver quantos % da versão atual já estão prontos.* |
| **`/gsd-discuss-phase`** | Conversar sobre a Fase | Faz perguntas e alinha com você os detalhes e regras de negócio antes de planejar. | *A próxima fase é "Criar Login", você usa para definir se o login será por e-mail, Google ou ambos.* |
| **`/gsd-plan-phase`** | Planejar Fase | Cria um plano detalhado (`PLAN.md`) dividindo a fase em tarefas técnicas organizadas. | *Depois de discutir o login, você gera o plano técnico passo a passo antes de escrever código.* |
| **`/gsd-execute-phase`** | Executar Fase | Põe a mão na massa: cria/edita os arquivos e implementa tudo que foi planejado. | *Você aprovou o plano do login e quer que o assistente programe tudo de uma vez.* |
| **`/gsd-verify-work`** | Verificar Trabalho | Guia você em um checklist de testes manuais e perguntas para garantir que tudo funciona. | *O login acabou de ser feito; o assistente te ajuda a testar se o formulário realmente autentica.* |
| **`/gsd-quick`** | Tarefa Rápida | Executa uma tarefa pequena/média com salvamento atômico sem criar uma fase inteira. | *"Mude a cor do botão principal para azul e ajuste o padding do cabeçalho."* |
| **`/gsd-fast`** | Super Rápido | Executa um ajuste mínimo imediato na conversa sem agentes auxiliares. | *"Corrija a digitação na linha 25 do arquivo main.py."* |
| **`/gsd-autonomous`** | Modo Autônomo | Roda todas as fases restantes do projeto de forma 100% autônoma. | *Você já definiu todo o roadmap e quer que ele faça fase por fase até terminar.* |

---

## 🗺️ 2. Gestão de Fases e Roadmap

| Comando | Nome em Português | O que faz? | Exemplo de Caso de Uso |
| :--- | :--- | :--- | :--- |
| **`/gsd-phase`** | Gerenciar Fases | Permite adicionar, editar, reordenar ou remover fases do `ROADMAP.md`. | *Você percebeu que precisa de uma fase extra de "Integração de Pagamentos" entre as fases 2 e 3.* |
| **`/gsd-spec-phase`** | Especificar Fase | Escreve uma especificação de requisitos (`SPEC.md`) para reduzir ambiguidades. | *Para uma fase complexa de envio de e-mails em massa, mapeia todos os limites e regras.* |
| **`/gsd-mvp-phase`** | Fase em MVP | Planeja a fase focando no menor produto viável funcional (corta excessos). | *Você quer entregar a tela de relatórios bem simples primeiro, sem gráficos pesados.* |
| **`/gsd-pause-work`** | Pausar Trabalho | Salva um snapshot do contexto atual para você parar e continuar outro dia. | *Fim do expediente: você precisa sair e quer registrar onde parou no meio de uma tarefa.* |
| **`/gsd-resume-work`** | Retomar Trabalho | Restaura todo o contexto de onde você parou na última sessão. | *Você voltou no dia seguinte e quer continuar o trabalho exatamente de onde parou.* |
| **`/gsd-workstreams`** | Fluxos Paralelos | Gerencia múltiplas frentes de trabalho ou tarefas simultâneas. | *Uma pessoa focada no Frontend e outra no Backend ao mesmo tempo.* |

---

## 🏁 3. Ciclo de Vida do Projeto (Milestones / Versões)

| Comando | Nome em Português | O que faz? | Exemplo de Caso de Uso |
| :--- | :--- | :--- | :--- |
| **`/gsd-new-project`** | Novo Projeto | Inicializa um projeto do absoluto zero, criando a pasta `.planning/` e o `PROJECT.md`. | *Você acabou de dar `git init` numa pasta vazia e quer montar todo o projeto.* |
| **`/gsd-onboard`** | Integrar Projeto | Mapeia um código legado/existente e cria o planejamento para ele. | *Você já tem um sistema com 50 arquivos e quer usar o GSD nele a partir de agora.* |
| **`/gsd-new-milestone`** | Nova Versão/Marco | Cria um novo ciclo de entrega após o anterior ser concluído (ex: Versão 2.0). | *A versão v1.0 foi entregue e agora você vai começar a planejar a versão v2.0.* |
| **`/gsd-complete-milestone`** | Concluir Versão | Finaliza, arquiva os relatórios e prepara o repositório para o próximo ciclo. | *Todas as fases da v1.0 foram concluídas e testadas com sucesso.* |
| **`/gsd-milestone-summary`** | Resumo da Versão | Gera um documento completo com tudo o que foi feito na versão. | *Gerar um relatório de lançamento (Release Notes) para mostrar à equipe ou clientes.* |

---

## 🔍 4. Qualidade, Testes e Correção de Bugs

| Comando | Nome em Português | O que faz? | Exemplo de Caso de Uso |
| :--- | :--- | :--- | :--- |
| **`/gsd-code-review`** | Revisão de Código | Analisa os arquivos alterados procurando bugs, problemas de performance e más práticas. | *Antes de subir o código para produção, você pede uma auditoria de qualidade.* |
| **`/gsd-debug`** | Depurar Problema | Inicia uma investigação metódica para achar a causa raiz de um erro persistente. | *A aplicação está dando `NullPointerException` ou crashando sem motivo óbvio.* |
| **`/gsd-add-tests`** | Adicionar Testes | Cria testes unitários e de integração baseados nas regras da fase. | *Criou uma função de cálculo de impostos e quer garantir testes para vários cenários.* |
| **`/gsd-audit-fix`** | Auditar e Corrigir | Varre o projeto em busca de falhas, classifica o que achou e já aplica correções. | *Rodar uma limpeza geral de erros antes de finalizar a fase.* |
| **`/gsd-audit-uat`** | Auditar Critérios | Checa se tudo o que o usuário/cliente pediu foi realmente implementado. | *Conferir se nenhum requisito da fase ficou esquecido para trás.* |
| **`/gsd-ui-review`** | Revisão de Interface | Audita a parte visual (layout, cores, contraste, responsividade e alinhamentos). | *Avaliar se a tela do dashboard está esteticamente moderna e bem alinhada.* |
| **`/gsd-secure-phase`** | Verificar Segurança | Faz uma varredura de segurança contra injeções, vazamentos e vulnerabilidades. | *Garantir que a API não expõe senhas ou tokens sensíveis no código.* |

---

## 💡 5. Ideação, Design e Prototipagem

| Comando | Nome em Português | O que faz? | Exemplo de Caso de Uso |
| :--- | :--- | :--- | :--- |
| **`/gsd-explore`** | Explorar Ideias | Debate ideias e arquiteturas antes de você bater o martelo. | *"Qual é o melhor banco de dados para esse caso: PostgreSQL ou MongoDB?"* |
| **`/gsd-sketch`** | Rascunho de Tela | Gera mockups visuais em HTML para validar o visual da tela antes de programar o app real. | *Criar um protótipo visual de uma tela de perfil para ver se fica bonita.* |
| **`/gsd-spike`** | Experimento Rápido | Cria um teste de conceito isolado para validar se uma biblioteca funciona. | *Testar se uma biblioteca de reconhecimento de voz funciona bem no Windows.* |

---

## 📦 6. Git, Documentação e Utilidades

| Comando | Nome em Português | O que faz? | Exemplo de Caso de Uso |
| :--- | :--- | :--- | :--- |
| **`/gsd-ship`** | Entregar/Publicar | Prepara o código, roda revisões finais e prepara o Pull Request (PR) para merge. | *Tudo está testado e pronto para ser enviado para a branch `main`.* |
| **`/gsd-pr-branch`** | Criar Branch de PR | Cria uma branch limpa sem os arquivos internos de planejamento para facilitar o review. | *Abrir um PR limpo no GitHub focado apenas no código de produção.* |
| **`/gsd-undo`** | Desfazer Alterações | Reverte commits de uma fase com segurança caso algo dê errado. | *A implementação de uma biblioteca quebrou o projeto e você quer voltar ao estado anterior.* |
| **`/gsd-docs-update`** | Atualizar Docs | Atualiza os arquivos `README.md` e documentações com base no código novo. | *Você adicionou 3 rotas novas na API e quer atualizar a documentação automaticamente.* |
| **`/gsd-stats`** | Ver Estatísticas | Exibe métricas de velocidade, commits, tarefas e progresso do repositório. | *Ver estatísticas sobre quantas tarefas foram concluídas na semana.* |
| **`/gsd-config`** / **`/gsd-settings`** | Configurações | Ajusta as preferências do GSD (modelos, comportamento de subagentes, etc.). | *Ativar ou desativar passos automáticos do fluxo de trabalho.* |
| **`/gsd-help`** | Ajuda | Exibe o menu com todos os comandos disponíveis. | *Consultar a lista rápida de comandos a qualquer momento.* |

---

> 💡 **Dica de Ouro:** Na maioria das vezes, você só precisa digitar **`/gsd-next`** ou **`/gsd-progress`**! O assistente identifica o que deve ser feito e te conduz no melhor caminho.
