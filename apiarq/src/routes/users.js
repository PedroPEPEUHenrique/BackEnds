const { Router } = require("express");
const prisma = require("../database");

const router = Router()

router.get("/", async (req, res) => {
  const users = await prisma.user.findMany()
  res.json(users)
})

router.post("/", async (req, res) => {
  const { name, email } = req.body
  const newUser = await prisma.user.create({
    data: {
      name,
      email
    }
  })
  res.status(201).json(newUser)
})

router.get("/:id", async (req, res) => {
  const user = await prisma.user.findUnique({
    where: {
      id: +req.params.id
    },
    include: {
      posts: true
    }
  })
  res.json(user)
})

router.put("/:id", async (req, res) => {
  const { name, email } = req.body
  const updatedUser = await prisma.user.update({
    data: { name, email },
    where: { id: Number(req.params.id) }
  })
  res.json(updatedUser)
})

router.delete("/:id", async (req, res) => {
  const deletedUser = await prisma.user.delete({
    where: { id: Number(req.params.id) }
  })
  res.json({ deletedUser })
})

module.exports = router