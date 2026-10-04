# DUB — o Mochi

Um blob que fica calmo no canto do ecrã. Tem o mesmo comportamento da KIK, mas um design abstrato.
A KIK original continua intacta em `../KIK`.

Abre com o atalho **DUB** no ambiente de trabalho. Fecha com **botão direito → Sair**.

## Modos (clique para trocar)
- **Trabalho**: está sentado à secretaria preta com o portátil e escreve com as maozinhas quando há Claudes a trabalhar.
  - O candeeiro cogumelo acende sozinho à noite (entre as 19h e as 7h).
  - Os adereços mudam de vez em quando (a cada 15 a 40 minutos): chá a fumegar, um vinil, uma cassete ou nada.
- **Música**: está sentado no chão, ligado a um walkman, e achata-se devagar no beat. Quando a música aquece, fecha os olhos. Nos drops, leva a mão ao phone.

## Avisos
- Quando um Claude termina, faz um polegar para cima e mostra um balão.
- Quando um Claude precisa de ti, mostra-te o telemóvel. Para isto é preciso o hook opcional da KIK (ver `../KIK/LEIA-ME.md`), que serve as duas apps.

## Consumo do Claude (5h e semanal)
- Duas barrinhas no canto inferior esquerdo (**5H** e **7D**). Verde até 80%, coral a partir daí e a piscar acima de 95%. Ficam cinzentas se não houver novidades há mais de 1h.
- No botão direito vês a percentagem e a hora do reset de cada uma.
- **Consumo no ecrã** (botão direito) tem três opções: **Desligado**, **Barras pequenas** (as de cima) e **Barras grandes com %**, duas barras horizontais com a percentagem escrita. As grandes alargam a janela do lado esquerdo, e o DUB não se mexe.
- Aos **80%** o DUB mostra um balão, uma vez por janela (a das 5h e a semanal avisam em separado).
- Os dados vêm da status line do Claude Code: `dub_statusline.py` guarda os valores em `~/.dub/usage.json` e o DUB só lê esse ficheiro. Para ativar, põe isto no `~/.claude/settings.json`:
  ```json
  "statusLine": { "type": "command", "command": "python \"C:\\caminho\\para\\dub_statusline.py\"" }
  ```
- Só se atualiza com um Claude aberto e depois da primeira resposta da sessão. Só existe para subscrições Pro e Max.

## Instalar noutro computador
- Corre `installer\Output\DUB-Setup.exe`. Instala só para o teu utilizador (sem administrador), cria o atalho e pode ligar o consumo do Claude e o arranque com o Windows.
- Para voltar a gerar o instalador depois de mexeres no código: `installer\build.ps1` (precisa de Python com pyinstaller, pillow, pycaw, comtypes e aalink, e do Inno Setup 6).
- O instalador não está assinado, por isso o Windows SmartScreen pode avisar na primeira vez ("Mais informações" → "Executar mesmo assim").
- Desinstalar: Definições → Aplicações → DUB. Tira a status line que o instalador pôs, e os teus dados em `~/.dub/` ficam.

## Visual (botão direito)
- **Cor**: 15 tons.
  - Claros: Mochi, Matcha, Hojicha, Ube, Névoa, Sakura, Momo, Yuzu, Kinako, Menta e Sora.
  - Escuros: Sésamo preto, Azuki, Café e Sumi (com olhos âmbar).
- O ícone do atalho **DUB** atualiza-se sozinho com a cor e o boné que escolheres.
- **Boné**: liga ou desliga.
- **Bochechas**: liga ou desliga (já vêm discretas, num tom próximo da cor do corpo).

**Arrastar** muda-o de sítio. O **botão direito** dá acesso aos Claudes, aos modos, aos sons, ao tamanho e ao Ableton Link.
Tudo é só leitura e local, e os dados ficam em `~/.dub/`.
