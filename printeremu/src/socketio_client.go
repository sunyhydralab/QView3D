package src

import (
	"encoding/json"
	"log"
	"net/url"
	"time"

	"sync"

	"github.com/gorilla/websocket"
)

type SocketIOMessage struct {
	Type int      `json:"type"`
	Event string   `json:"event,omitempty"`
	Data interface{} `json:"data,omitempty"`
	Nsp string `json:"nsp,omitempty"`
}

type SocketIOClient struct {
	conn *websocket.Conn
	send chan []byte
	close    chan struct{}
	handlers map[string]func(interface{})
	wg       sync.WaitGroup	
}

func NewClient() *SocketIOClient {
	return &SocketIOClient{
		send: make(chan []byte),
		handlers: make(map[string]func(interface{})),
		close:    make(chan struct{}),
	}
}

func (c *SocketIOClient) Connect(uri string) error {
	c.handlers = make(map[string]func(interface{}))

	u, err := url.Parse(uri)
	if err != nil {
		return err
	}

	switch u.Scheme {
	case "http", "ws":
		u.Scheme = "ws"
	case "https", "wss":
		u.Scheme = "wss"
	}
	
	u.Path = "/socket.io/"
	u.RawQuery = "EIO=4&transport=websocket"

	conn, _, err := websocket.DefaultDialer.Dial(u.String(), nil)

	if err != nil {
		return err
	}

	c.conn = conn
	c.wg.Add(2)

	go c.readPump()
	go c.StartWritePump()

	c.send <- []byte("40")

	return nil
}

func (c *SocketIOClient) readPump() {
	defer func() {
		close(c.close)
		c.wg.Done()
		c.conn.Close()
	}()

	for {
		_, message, err := c.conn.ReadMessage()

		if err != nil {
			log.Printf("read error: %v", err)
			return
		}

		if len(message) > 0 {
			switch message[0] {
			case '0': // connection
				log.Println("Connnected to server")
			case '1': // keepalive?
				c.send <- []byte("3")
			case '4': // message
				if len(message) > 1 {
					c.handleMessage(message[1:])
				}
			}
		}
	}
}

func (c *SocketIOClient) StartWritePump() {
	defer func() {
		c.wg.Done()
		c.conn.Close()
	}()

	
	ticker := time.NewTicker(10 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case message := <-c.send:
			err := c.conn.WriteMessage(websocket.TextMessage, message)
			if err != nil {
				log.Println("write error:", err)
				return
			}
		case <-ticker.C:
			err := c.conn.WriteMessage(websocket.TextMessage, []byte("2"))
			if err != nil {
				log.Println("ping error:", err)
				return
			}
		case <-c.close:
			return
		}
	}
}


func (c *SocketIOClient) On(event string, handler func(interface{})) {
	c.handlers[event] = handler
}

func (c *SocketIOClient) Emit(event string, data interface{}) error {
	msg := SocketIOMessage{
		Type: 4,
		Event: event,
		Data: data,
		Nsp: "/",
	}

	payload, err := json.Marshal(msg)

	if err != nil {
		log.Println("Failed to marshal message:", err)
		return err
	}

	c.send <- payload

	return nil
}

func (c *SocketIOClient) handleMessage(message []byte) {
	if len(message) > 1 && message[0] == '0' {
		message = message[1:]
	}

	var msg SocketIOMessage

	if err := json.Unmarshal(message, &msg); err != nil {
		log.Println("Failed to unmarshal message:", err)
		//log.Println("Raw message:", string(message)) 
		return
	}

	if handler, ok := c.handlers[msg.Event]; ok {
		handler(msg.Data)
	} else {
		//log.Println("No handler registered for event:", msg.Event)
	}
}

func (c *SocketIOClient) Close() {
	close(c.close)
	c.wg.Wait()
}