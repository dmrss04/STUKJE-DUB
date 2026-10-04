<p align="center">
  <img src="docs/banner.png" alt="DUB, o Mochi, em várias cores" width="100%">
</p>

# DUB

**DUB é um blob calmo que vive no canto do ecrã do Windows.** Enquanto trabalhas, diz-te o que os teus [Claude Code](https://claude.com/claude-code) estão a fazer. Quando ouves música, abana a cabeça ao ritmo.

É um companheiro discreto: não pede atenção, só aparece quando tem algo útil para te dizer.

## O que faz

| | |
|---|---|
| **Modo trabalho** | Senta-se à secretaria com o portátil e escreve quando há Claudes a trabalhar. Um quadrado por cada Claude mostra o estado: verde a trabalhar, cinzento livre, coral a precisar de ti. |
| **Modo música** | Senta-se no chão com um walkman e achata-se ao beat do que estiver a tocar no PC. Fecha os olhos quando a música aquece. |
| **Avisos** | Quando um Claude termina, faz um polegar para cima. Quando precisa de ti (uma permissão, por exemplo), mostra o telemóvel e um balão. |
| **Consumo do Claude** | Barras com o consumo da janela de **5 horas** e da **semana**, sempre à vista. Avisa uma vez quando passam dos **80%**. |
| **Personalização** | 15 cores, boné, bochechas e 4 tamanhos. O ícone do atalho muda com a cor que escolheres. |

Clica no DUB para trocar de modo, arrasta-o para mudar de sítio e usa o **botão direito** para o menu (Claudes, consumo, cores, sons, tamanho e sair).

## Consumo do Claude

O DUB mostra duas barras, **5H** e **7D**, que ficam verdes até aos 80%, passam a coral a partir daí e piscam acima dos 95%. No menu (botão direito → **Consumo no ecrã**) escolhes entre:

- **Barras pequenas**: discretas, no canto.
- **Barras grandes com %**: com a percentagem escrita.
- **Desligado**.

No mesmo menu vês a hora a que cada janela faz reset.

**Como funciona:** o Claude Code envia os limites de consumo à *status line*. O pequeno programa `dub_statusline` guarda esses valores em `~/.dub/usage.json` e o DUB só lê esse ficheiro. Não há contas, tokens nem pedidos à internet.

**Limites a conhecer:**
- Só existe para subscrições Claude **Pro** e **Max**.
- Atualiza-se enquanto tiveres um Claude aberto, depois da primeira resposta da sessão. Se os dados tiverem mais de 1 hora, as barras ficam cinzentas.

## Instalação

### Instalador (recomendado)

Gera o `DUB-Setup.exe` (ver [Compilar o instalador](#compilar-o-instalador)) e corre-o. Instala só para o teu utilizador, sem precisar de administrador, e deixa escolher:

- atalho no ambiente de trabalho;
- mostrar o consumo do Claude (liga a status line do Claude Code);
- abrir o DUB quando o Windows arranca.

Se já tiveres uma status line no Claude Code, o instalador não lhe toca e avisa. Para desinstalar, usa **Definições → Aplicações → DUB**.

> O instalador não está assinado, por isso o Windows SmartScreen pode avisar na primeira vez. Escolhe **Mais informações → Executar mesmo assim**.

### A partir do código

Precisas de Windows 10 ou 11 e Python 3.12 ou superior.

```powershell
pip install pycaw comtypes aalink
python dub.py
```

Para ver o consumo do Claude a partir do código, acrescenta isto ao `~/.claude/settings.json` (ajusta o caminho):

```json
"statusLine": {
  "type": "command",
  "command": "python \"C:\\caminho\\para\\dub_statusline.py\""
}
```

## Privacidade

Tudo é local e só de leitura. O DUB não envia nada para a internet.

- **Áudio:** lê apenas o medidor de volume do Windows. Não grava nem interceta som.
- **Claudes:** lê apenas `~/.claude/sessions/*.json`, o estado que o Claude Code já escreve.
- **Consumo:** lê apenas `~/.dub/usage.json`.
- **Ableton Link:** desligado por defeito, opcional no menu.

As preferências ficam em `~/.dub/`.

## Compilar o instalador

Precisas de Python com `pyinstaller`, `pillow`, `pycaw`, `comtypes` e `aalink`, e do [Inno Setup 6](https://jrsoftware.org/isinfo.php) (`winget install JRSoftware.InnoSetup`).

```powershell
.\installer\build.ps1
```

O resultado fica em `installer\Output\DUB-Setup.exe`.

## Estrutura

| Ficheiro | Para que serve |
|---|---|
| `dub.py` | A aplicação: sprite em pixel art, modos, avisos e menu. |
| `dub_statusline.py` | Status line do Claude Code que guarda o consumo para o DUB. |
| `installer/` | Script do instalador (Inno Setup), imagens do assistente e `build.ps1`. |
| `DUB.spec` | Compilação de um único `DUB.exe` portátil com PyInstaller. |
| `LEIA-ME.md` | Notas de uso mais detalhadas. |

## Licença

[MIT](LICENSE)
