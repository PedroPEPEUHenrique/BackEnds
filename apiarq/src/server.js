
require('dotenv').config()

const express = require("express");
const userRouter = require("./routes/users");
const postRouter = require("./routes/posts");

const app = express();

app.use(express.json());

app.use("/api/users", userRouter);
app.use("/api/posts", postRouter);

const PORT = process.env.PORT || 3001
app.listen(PORT, () => console.log(`Servidor iniciado!\nRodando em http://localhost:${PORT} \nPrecione Ctrl+C para encerrar o servidor web.`))
