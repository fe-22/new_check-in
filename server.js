const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');

const app = express();
const PORT = process.env.PORT || 3000;

// Middlewares
app.use(cors());
app.use(bodyParser.json());

// Dados em memória (para teste)
let clientes = [];
let checkins = [];
let pontos = {};

// Rotas da API
app.get('/', (req, res) => {
  res.json({
    message: '✅ Sistema de Check-in e Fidelidade Online!',
    version: '1.0.0',
    endpoints: {
      checkin: 'POST /api/checkin',
      clientes: 'GET /api/clientes',
      pontos: 'GET /api/pontos/:clienteId'
    }
  });
});

// Registrar check-in
app.post('/api/checkin', (req, res) => {
  const { clienteId, clienteNome } = req.body;
  
  if (!clienteId) {
    return res.status(400).json({ error: 'clienteId é obrigatório' });
  }

  // Registrar cliente se não existir
  if (!clientes.find(c => c.id === clienteId)) {
    clientes.push({ id: clienteId, nome: clienteNome || `Cliente ${clienteId}` });
  }

  // Registrar check-in
  const checkin = {
    id: Date.now(),
    clienteId,
    data: new Date().toISOString(),
    pontos: 10
  };
  
  checkins.push(checkin);

  // Acumular pontos
  pontos[clienteId] = (pontos[clienteId] || 0) + 10;

  res.json({
    success: true,
    message: `Check-in realizado! +10 pontos`,
    checkin,
    totalPontos: pontos[clienteId]
  });
});

// Listar clientes
app.get('/api/clientes', (req, res) => {
  res.json({
    clientes: clientes.map(cliente => ({
      ...cliente,
      pontos: pontos[cliente.id] || 0
    }))
  });
});

// Ver pontos de um cliente
app.get('/api/pontos/:clienteId', (req, res) => {
  const { clienteId } = req.params;
  res.json({
    clienteId,
    pontos: pontos[clienteId] || 0,
    checkins: checkins.filter(c => c.clienteId === clienteId)
  });
});

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'OK', timestamp: new Date().toISOString() });
});

app.listen(PORT, () => {
  console.log(`🚀 Servidor rodando na porta ${PORT}`);
  console.log(`📋 Acesse: http://localhost:${PORT}`);
  console.log(`🌐 Health check: http://localhost:${PORT}/health`);
});