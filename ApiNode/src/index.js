require('dotenv').config()
const express = require('express')
const authRouter = require('./routes/auth')
const apiRouter = require('./routes/api')
const errorMiddleware = require('./middlewares/error-middleware')

const app = express()

app.use(express.json())

app.use('/auth', authRouter)
app.use('/api', apiRouter)

app.use(errorMiddleware)

const PORT = process.env.PORT || 3001
app.listen(PORT, () => console.log(`Servidor iniciado!\nRodando em http://localhost:${PORT} \nPrecione Ctrl+C para encerrar o servidor web.`))