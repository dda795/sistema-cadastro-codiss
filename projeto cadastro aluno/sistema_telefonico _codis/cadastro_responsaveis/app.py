from flask import Flask, render_template, request, redirect, jsonify, url_for
from data.alunos import ALUNOS, TURMAS, AGRO_3_A, AGRO_3_B
import json
import os

app = Flask(__name__)

# ============================================================
# ARQUIVO DE CADASTROS
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ARQUIVO_CADASTROS = os.path.join(
    BASE_DIR,
    "data",
    "cadastros.json"
)

print("=" * 60)
print("SISTEMA DE CADASTRO - IFPI / CODIS")
print("Arquivo de cadastros:")
print(ARQUIVO_CADASTROS)
print("Arquivo existe:", os.path.exists(ARQUIVO_CADASTROS))
print("=" * 60)


# ============================================================
# LISTA DE PARENTESCOS
# ============================================================

parentescos = [
    "Pai",
    "Mãe",
    "Avô",
    "Avó",
    "Irmão",
    "Irmã",
    "Tio",
    "Tia",
    "Responsável legal",
    "Outro"
]


# ============================================================
# CARREGAR CADASTROS
# ============================================================

def carregar_cadastros():

    if not os.path.exists(ARQUIVO_CADASTROS):
        return {}

    try:
        with open(
            ARQUIVO_CADASTROS,
            "r",
            encoding="utf-8"
        ) as arquivo:

            conteudo = arquivo.read().strip()

            if not conteudo:
                return {}

            return json.loads(conteudo)

    except (json.JSONDecodeError, OSError) as erro:

        print("ERRO AO LER cadastros.json:", erro)

        return {}


# ============================================================
# SALVAR CADASTROS
# ============================================================

def salvar_cadastros(cadastros):

    pasta = os.path.dirname(ARQUIVO_CADASTROS)

    os.makedirs(
        pasta,
        exist_ok=True
    )

    with open(
        ARQUIVO_CADASTROS,
        "w",
        encoding="utf-8"
    ) as arquivo:

        json.dump(
            cadastros,
            arquivo,
            ensure_ascii=False,
            indent=4
        )

    print("CADASTROS SALVOS EM:")
    print(ARQUIVO_CADASTROS)


# ============================================================
# DESCOBRIR TURMA
# ============================================================

def descobrir_turma(matricula):

    if matricula in AGRO_3_A:
        return "3º Agropecuária A"

    if matricula in AGRO_3_B:
        return "3º Agropecuária B"

    for codigo, turma in TURMAS.items():

        if matricula.startswith(codigo):
            return turma

    return "Turma não identificada"


# ============================================================
# BUSCAR ALUNO
# ============================================================

def buscar_aluno(matricula):

    nome = ALUNOS.get(matricula)

    if nome is None:
        return None, None

    turma = descobrir_turma(matricula)

    return nome, turma


# ============================================================
# PÁGINA INICIAL
# ============================================================

@app.route("/")
def index():

    return render_template("index.html")


# ============================================================
# CADASTRO
# ============================================================

@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():

    if request.method == "POST":

        matricula = request.form.get(
            "matricula",
            ""
        ).strip()

        responsavel = request.form.get(
            "responsavel",
            ""
        ).strip()

        parentesco = request.form.get(
            "parentesco",
            ""
        ).strip()

        telefone = request.form.get(
            "telefone",
            ""
        ).strip()

        # ----------------------------------------------------
        # VALIDAÇÕES
        # ----------------------------------------------------

        if not matricula:
            return "Matrícula é obrigatória.", 400

        if not responsavel:
            return "Nome do responsável é obrigatório.", 400

        if not parentesco:
            return "Parentesco é obrigatório.", 400

        if parentesco not in parentescos:
            return "Parentesco inválido.", 400

        if not telefone:
            return "Telefone do responsável é obrigatório.", 400

        # ----------------------------------------------------
        # VERIFICA ALUNO
        # ----------------------------------------------------

        nome, turma = buscar_aluno(matricula)

        if nome is None:
            return "Matrícula não encontrada.", 400

        # ----------------------------------------------------
        # CARREGA CADASTROS
        # ----------------------------------------------------

        cadastros = carregar_cadastros()

        # ----------------------------------------------------
        # EVITA CADASTRO DUPLICADO
        # ----------------------------------------------------

        if matricula in cadastros:

            return """
            <!DOCTYPE html>
            <html lang="pt-BR">

            <head>
                <meta charset="UTF-8">
                <title>Cadastro já realizado</title>
            </head>

            <body style="
                font-family: Arial, sans-serif;
                text-align: center;
                padding: 60px;
            ">

                <h2>Cadastro já realizado</h2>

                <p>
                    Esta matrícula já possui um cadastro
                    de responsável.
                </p>

                <p>
                    Se houver algum erro nos dados,
                    procure a administração.
                </p>

                <br>

                <a href="/">
                    Voltar para o início
                </a>

            </body>
            </html>
            """, 409

        # ----------------------------------------------------
        # SALVA CADASTRO
        # ----------------------------------------------------

        cadastros[matricula] = {
            "nome": nome,
            "turma": turma,
            "responsavel": responsavel,
            "parentesco": parentesco,
            "telefone": telefone
        }

        salvar_cadastros(cadastros)

        print("=" * 60)
        print("NOVO CADASTRO")
        print("Aluno:", nome)
        print("Matrícula:", matricula)
        print("Turma:", turma)
        print("Responsável:", responsavel)
        print("Parentesco:", parentesco)
        print("Telefone:", telefone)
        print("=" * 60)

        return redirect("/")

    return render_template(
        "cadastro.html",
        parentescos=parentescos
    )


# ============================================================
# BUSCAR ALUNO - API
# ============================================================

@app.route("/buscar-aluno")
def buscar_aluno_api():

    matricula = request.args.get(
        "matricula",
        ""
    ).strip()

    nome, turma = buscar_aluno(matricula)

    if nome:

        return jsonify({
            "encontrado": True,
            "nome": nome,
            "turma": turma
        })

    return jsonify({
        "encontrado": False
    })


# ============================================================
# PAINEL ADMINISTRATIVO
# ============================================================

@app.route("/admin")
def admin():

    cadastros = carregar_cadastros()

    # --------------------------------------------------------
    # ESTATÍSTICAS
    # --------------------------------------------------------

    total_alunos = len(ALUNOS)

    cadastrados = sum(
        1
        for matricula in ALUNOS
        if matricula in cadastros
    )

    pendentes = total_alunos - cadastrados

    # --------------------------------------------------------
    # LISTA DE ALUNOS
    # --------------------------------------------------------

    alunos = []

    for matricula, nome in ALUNOS.items():

        cadastro = cadastros.get(matricula)

        turma = descobrir_turma(matricula)

        alunos.append({
            "matricula": matricula,
            "nome": nome,
            "turma": turma,
            "cadastrado": cadastro is not None,
            "cadastro": cadastro
        })

    # --------------------------------------------------------
    # LISTA DE TURMAS
    # --------------------------------------------------------

    turmas = sorted(
        set(
            aluno["turma"]
            for aluno in alunos
        )
    )

    print(
        "PAINEL ADMIN:",
        cadastrados,
        "cadastrados /",
        pendentes,
        "pendentes"
    )

    return render_template(
        "admin.html",
        alunos=alunos,
        total_alunos=total_alunos,
        cadastrados=cadastrados,
        pendentes=pendentes,
        turmas=turmas
    )


# ============================================================
# EDITAR CADASTRO
# ============================================================

@app.route("/editar/<matricula>", methods=["GET", "POST"])
def editar_cadastro(matricula):

    nome, turma = buscar_aluno(matricula)

    if nome is None:
        return "Aluno não encontrado.", 404

    cadastros = carregar_cadastros()

    if matricula not in cadastros:
        return "Este aluno ainda não possui cadastro.", 404

    cadastro_atual = cadastros[matricula]

    # --------------------------------------------------------
    # SALVAR ALTERAÇÕES
    # --------------------------------------------------------

    if request.method == "POST":

        responsavel = request.form.get(
            "responsavel",
            ""
        ).strip()

        parentesco = request.form.get(
            "parentesco",
            ""
        ).strip()

        telefone = request.form.get(
            "telefone",
            ""
        ).strip()

        if not responsavel:
            return "Nome do responsável é obrigatório.", 400

        if not parentesco:
            return "Parentesco é obrigatório.", 400

        if parentesco not in parentescos:
            return "Parentesco inválido.", 400

        if not telefone:
            return "Telefone do responsável é obrigatório.", 400

        cadastros[matricula] = {
            "nome": nome,
            "turma": turma,
            "responsavel": responsavel,
            "parentesco": parentesco,
            "telefone": telefone
        }

        salvar_cadastros(cadastros)

        print("=" * 60)
        print("CADASTRO ATUALIZADO")
        print("Aluno:", nome)
        print("Matrícula:", matricula)
        print("Responsável:", responsavel)
        print("Parentesco:", parentesco)
        print("Telefone:", telefone)
        print("=" * 60)

        return redirect(url_for("admin"))

    return render_template(
        "editar.html",
        matricula=matricula,
        nome=nome,
        turma=turma,
        cadastro=cadastro_atual,
        parentescos=parentescos
    )


# ============================================================
# EXCLUIR CADASTRO
# ============================================================

@app.route("/excluir/<matricula>", methods=["POST"])
def excluir_cadastro(matricula):

    cadastros = carregar_cadastros()

    if matricula not in cadastros:
        return "Cadastro não encontrado.", 404

    cadastro_excluido = cadastros.pop(matricula)

    salvar_cadastros(cadastros)

    print("=" * 60)
    print("CADASTRO EXCLUÍDO")
    print(
        "Aluno:",
        cadastro_excluido.get("nome", "")
    )

    print(
        "Matrícula:",
        matricula
    )

    print("=" * 60)

    return redirect(url_for("admin"))


# ============================================================
# INICIAR SISTEMA
# ============================================================

if __name__ == "__main__":

     app.run(host="0.0.0.0", port=5000, debug=True)