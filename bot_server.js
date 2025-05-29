const venom = require('venom-bot');
const express = require('express');
const bodyParser = require('body-parser');
const app = express();
app.use(bodyParser.json());

venom.create().then((client) => {
  app.post('/enviar', (req, res) => {
    const { numero, mensagem } = req.body;
    client.sendText(`${numero}@c.us`, mensagem)
      .then(() => res.send("Enviado"))
      .catch((err) => res.status(500).send(err));
  });

  app.listen(3001, () => {
    console.log("Bot WhatsApp rodando na porta 3001");
  });
});