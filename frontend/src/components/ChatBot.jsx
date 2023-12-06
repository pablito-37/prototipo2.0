import React, { useState, useEffect } from "react";

const Chatbot = () => {
  const [chatMessages, setChatMessages] = useState([
    { id: 1, text: '¡Hola!', sender: 'bot' }
  ]);
  const [newMessage, setNewMessage] = useState("");

  useEffect(() => {
    // Sincronizar el estado con el localStorage
    localStorage.setItem("chatMessages", JSON.stringify(chatMessages));
  }, [chatMessages]);

  const sendMessage = async () => {
    try {
      // Enviar el mensaje del usuario al servidor
      const response = await fetch("http://localhost:5000/pregunta_respuesta", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          contexto: "principito",
          pregunta: newMessage,
          calificacion: 2,
        }),
      });

      if (response.ok) {
        const result = await response.json();
        // Actualizar el estado y sincronizar con el localStorage
        setChatMessages((prevMessages) => [
          ...prevMessages,
          { id: Date.now(), text: newMessage, sender: "user" }, // Agregar mensaje del usuario
          { id: Date.now() + 1, text: result.respuesta, sender: "bot" }, // Agregar respuesta del bot
        ]);
        setNewMessage("");
      } else {
        console.error("Error al enviar la pregunta al servidor.");
      }
    } catch (error) {
      console.error("Error de red:", error);
    }
  };


  return (
    <div className="max-w-md mx-auto mt-8 p-4 bg-gray-100 border rounded">
      <div className="space-y-2 max-h-96 overflow-y-auto">
        {chatMessages.map((message) => (
          <div
            key={message.id}
            className={`p-2 rounded ${message.sender === "bot"
              ? "bg-yellow-200 text-left"
              : "bg-green-200 text-right"
              }`}
          >
            <div className="flex justify-between">
              <span className="text-xs font-bold">
                {message.sender === "bot" ? "Bot" : "User"}
              </span>
              <span>{message.text}</span>
            </div>
          </div>
        ))}
      </div>
      <div className="flex mt-4">
        <input
          className="flex-grow p-2 border rounded"
          value={newMessage}
          onChange={(e) => setNewMessage(e.target.value)}
        />
        <button
          className="ml-2 p-2 bg-green-500 text-white rounded"
          onClick={sendMessage}
        >
          Enviar
        </button>
      </div>
    </div>
  );


};

export default Chatbot;
