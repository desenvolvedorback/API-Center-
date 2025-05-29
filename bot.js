const venom = require('venom-bot');

venom.create().then((client) => start(client));

function start(client) {
  global.sendWhatsApp = (numero, mensagem) => {
    const numeroComDDI = `${numero}@c.us`; // exemplo: 5591999999999@c.us
    client.sendText(numeroComDDI, mensagem)
      .then(() => {
        console.log("Mensagem enviada para", numero);
      })
      .catch((err) => {
        console.error("Erro ao enviar mensagem:", err);
      });
  };
}