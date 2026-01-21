const HttpError = require('../errors/HttpError')
const uuid = require('uuid').v4

let books = [
  { id: '1', title: 'Programação web com Node e Express', author: 'Ethan Brown', quantityAvailable: 4 },
  { id: '2', title: 'Construindo Aplicações com NodeJS', author: 'William Bruno Moraes', quantityAvailable: 3 }
]

module.exports = {
  getAllBooks: () => books.map(book => ({ id: book.id, title: book.title, quantityAvailable: book.quantityAvailable })),

  getBookById: (id) => books.find(book => book.id === id),

  createBook: (title, author, quantityAvailable) => {
    const newBook = {
      id: uuid(),
      title,
      author,
      quantityAvailable
    }
    books.push(newBook)
    return newBook
  },

  updateBook: (id, updatedBook) => {
    const bookIndex = books.findIndex(book => book.id === id)
    if (bookIndex === -1) throw new HttpError(404, 'Livro não encontrado no sistema!')
    books[bookIndex] = { ...books[bookIndex], ...updatedBook }
    return books[bookIndex]
  },

  deleteBook: (id) => {
    const bookIndex = books.findIndex(book => book.id === id)
    if (bookIndex === -1) throw new HttpError(404, 'Livro não encontra no sistema!')
    const deletedBook = books[bookIndex]
    books = books.filter(book => book.id !== id)
    return deletedBook
  },

  takeBook: (id) => {
    const bookIndex = books.findIndex(book => book.id === id)
    if (bookIndex === -1) throw new HttpError(404, 'Livro não encontra no sistema!')
    books[bookIndex].quantityAvailable -= 1
  },

  returnBook: (id) => {
    const bookIndex = books.findIndex(book => book.id === id)
    if (bookIndex === -1) throw new HttpError(404, 'Livro não encontra no sistema!')
    books[bookIndex].quantityAvailable += 1
  }
}