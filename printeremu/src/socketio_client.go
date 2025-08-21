package src

import (
	"encoding/json"
	"fmt"
	"log"

	"github.com/gorilla/websocket"
)

// SocketIOClient represents a simple client for interacting with Socket.IO
type SocketIOClient struct {
	conn *websocket.Conn
	sid  string
}

// SocketIOMessage represents a message sent/received with Socket.IO
type SocketIOMessage struct {
	Event string      `json:"event"`
	Data  interface{} `json:"data"`
}

// NewSocketIOClient initializes and returns a new client instance.
func NewSocketIOClient() *SocketIOClient {
	return &SocketIOClient{}
}

// Connect establishes a WebSocket connection to the Socket.IO server.
func (c *SocketIOClient) Connect(serverURL string) error {
	// Open the connection
	conn, _, err := websocket.DefaultDialer.Dial(serverURL, nil)
	if err != nil {
		return fmt.Errorf("failed to connect to server: %v", err)
	}
	c.conn = conn
	log.Printf("Connected to %s", serverURL)
	return nil
}

// Send sends a message to the WebSocket server.
func (c *SocketIOClient) Send(message []byte) error {
	err := c.conn.WriteMessage(websocket.TextMessage, message)
	if err != nil {
		return fmt.Errorf("failed to send message: %v", err)
	}
	log.Printf("Sent: %s", string(message))
	return nil
}

// Receive listens for messages from the WebSocket server.
func (c *SocketIOClient) Receive() (string, error) {
	_, message, err := c.conn.ReadMessage()
	if err != nil {
		return "", fmt.Errorf("failed to read message: %v", err)
	}
	return string(message), nil
}

// HandleSocketIOHandshake handles the initial handshake response from the Socket.IO server.
func (c *SocketIOClient) HandleSocketIOHandshake(response string) error {
	if response[0] == '0' { // This is the Engine.IO handshake response
		log.Println("Received handshake response from the server.")
		// Send the "2" message to acknowledge and connect
		return c.Send([]byte("2"))
	}
	return fmt.Errorf("unexpected handshake response: %s", response)
}

// Emit sends an event with data (a JSON object) to the Socket.IO server.
func (c *SocketIOClient) Emit(event string, data interface{}) error {
	msg := SocketIOMessage{
		Event: event,
		Data:  data,
	}

	payload, err := json.Marshal(msg)
	if err != nil {
		return fmt.Errorf("failed to marshal message: %v", err)
	}

	// Socket.IO "42" prefix for events
	fullPayload := append([]byte("42"), payload...)
	return c.Send(fullPayload)
}

// Close closes the WebSocket connection.
func (c *SocketIOClient) Close() error {
	if c.conn != nil {
		err := c.conn.Close()
		if err != nil {
			return fmt.Errorf("failed to close connection: %v", err)
		}
		log.Println("Connection closed.")
	}
	return nil
}
