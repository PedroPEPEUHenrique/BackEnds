const uuid = require('uuid').v4

const bcrypt = require('bcrypt')

// const senha = bcrypt.hashSync('123456', 10)

const users = [
  { id: '1', name: 'Luiz', email: 'luiz@email.com', password: '123456' },
  { id: '2', name: 'Rassi', email: 'rassi@email.com', password: '0000' }
]

module.exports = {
  getAllUsers: () => users,

  getUserById: (id) => users.find(user => user.id === id),

  getUserByEmail: (email) => users.find(user => user.email === email),

  createUser: (name, email, password) => {
    const newUser = {
      id: uuid(),
      name,
      email,
      password: bcrypt.hashSync(password, 10)
    }
    users.push(newUser)
    return newUser
  }
}