const express = require('express');
const app = express();
const PORT = 3000;

app.use(express.json());

/**/

function validarCadastro(req, res,next){
    const{nome, idade, email, cep, senha, confirmSenha} = req.body;

    if(!nome){
        return res.status(400).json({error: "Erro de validação", field: "nome", message: "Nome é obrigatório"});
    }

    if(!email){
        return res.status(400).json({error: "Erro de validação", field: "email", message: "E-mail é obrigatório"});
    }

    const emailRegex = /^[^\s@]+@[^\a@]+\.[^\s@]+$/;
    if(!emailRegex.test(email)){
        return res.status(400).json({error: "Erro de validação", field: "email", message: "Formato de email inválido"});
    }

    if(!cep){
        return res.status(400).json({error: "Erro de validação", field: "cep", message: "CEP é obrigatório"})
    }

    const cepRegex = /^\d{8$/;
    if(!cepRegex.test(cep)){
        return res.status(400).json({error: "Erro de validação", field: "senha", message: "Senha é obrigatória"})
    }

    if (idade === undefined || isNaN(idade) || !Number.isInteger(idade) || idade < 16 || idade > 120){
        return res.status(400).json({error: "Erro de validação", field: "idade", message: "Idade inválida"})
    }
    
    if (senha.lenght < 6 || senha.lenght > 10){
        return res.status(400).json({error: "Erro de validação", field: "senha", message: "Senha inválida"})
    }
    if (senha !== confirmSenha){
        return res.status(400).json({error: "Erro de validação", field: "senha", message: "Senha inválida"})
    }

    next()
}

app.post('/api/v1/cadastros', validarCadastro , (req, res) => {
    const novoId = Math.random().toString(36).substring(2, 7);
    res.status(201).json({
        "id": novoId,
        "message": "Cadastro criado"
    });

});

app.listen(PORT, () =>{
    console.log(`Servidor rodando em http://localhost:${PORT}`);
});