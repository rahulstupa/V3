var express = require('express')
var app = express()
var http = require('http').createServer(app);
var io = require('socket.io')(http,{
        cors: {
                origin: "http://192.168.0.221:9090",
    methods: ["GET", "POST"],
    allowedHeaders: ["*"]
}}
);

http.listen(5100,'0.0.0.0');

io.on('connection', function(socket) {
  console.log('Client connected to the WebSocket');

  socket.on('disconnect', () => {
    console.log('Client disconnected');
  });
        socket.on("score", (data) => {
          console.log(data)
         io.emit("score", data)});
        socket.on("tracking", (data) => {
         io.emit("tracking", data)});
        socket.on("point", (data) => {
         io.emit("point", data)});
        socket.on("set", (data) => {
         io.emit("set", data)});
         socket.on("match", (data) => {
         io.emit("match", data)});
	socket.on("views", (data) => {
         io.emit("views", data)});
	socket.on("teamscore", (data) => {
         io.emit("teamscore", data)});


})

