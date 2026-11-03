// src/config/database.js
const { Sequelize } = require('sequelize');
const path = require('path');

// Using SQLite for the prototype; replace with Postgres/MySQL in production.
const sequelize = new Sequelize({
  dialect: 'sqlite',
  storage: path.join(__dirname, '../../database.sqlite'),
  logging: false,
});

module.exports = sequelize;
