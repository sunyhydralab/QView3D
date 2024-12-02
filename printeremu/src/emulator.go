package src

import (
	"bufio"
	"context"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"strings"
	"time"

	"github.com/gorilla/websocket"
)

type Event struct {
	Event string      `json:"event"`
	Data  interface{} `json:"data"`
}

// Main function to initialize and run the printer emulator
func main() {
	extruder, printer, err := Init(1, "Device1", "Test Printer", "HWID1234", "Printer1", "Active")
	if err != nil {
		log.Fatalf("Failed to initialize printer: %v", err)
	}
	RunCommand(extruder, printer)
}

// Init function initializes the Extruder and Printer
func Init(id int, device string, description string, hwid string, name string, status string) (*Extruder, *Printer, error) {
	//fmt.Println("Initializing printer...")

	position := Vector3{X: 100, Y: 27, Z: 76}
	extruder := NewExtruder(position, 250, 100, 125)

	// Create a new heatbed instance
	heatbed := &Heatbed{
		Temp:       60.0,  // Default initial temperature
		TargetTemp: 100.0, // Target temperature for the heatbed
	}

	printer, err := NewPrinter(id, device, description, hwid, name, status, time.Now().String(), extruder, heatbed)

	if err != nil {
		log.Fatal("Failed to create printer:", err)
	}

	//fmt.Println(printer.String())

	return extruder, printer, nil
}

func PostRegistry(printer *Printer) {
	printer.Heatbed.Length = printer.GetData("length").(float64)
	printer.Heatbed.Width = printer.GetData("width").(float64)
	printer.Extruder.MaxZHeight = printer.GetData("height").(float64)
	printer.Heatbed.Temp = printer.GetData("startTemp").(float64)
}

func RunConnection(ctx context.Context, extruder *Extruder, printer *Printer, settings *EmulatorSettings) {
	loadedAddress := func() string {
		if settings.DefaultAddress != "" && settings.DefaultPort != 0 {
			return fmt.Sprintf("%s:%d", settings.DefaultAddress, settings.DefaultPort)
		}
		return "127.0.0.1:8001" // default address
	}()

	serverURL := "ws://" + loadedAddress

	conn, _, err := websocket.DefaultDialer.Dial(serverURL, nil)

	if err != nil {
		log.Fatal("Failed to connect to server:", err)
	}

	defer conn.Close()

	fmt.Println("Connected to WebSocket server")

	pingTicker := time.NewTicker(5 * time.Second)
	defer pingTicker.Stop()

	for {
		select {
		case <-ctx.Done():
			fmt.Println("Context canceled, closing connection.")
			return
		case <-pingTicker.C:
			pingMessage := map[string]interface{}{
				"event": "ping",
				"data":  "alive",
			}

			jsonPingMessage, err := json.Marshal(pingMessage)

			if err != nil {
				log.Println("Failed to marshal ping message:", err)
				return
			}

			if err := conn.WriteMessage(websocket.TextMessage, jsonPingMessage); err != nil {
				log.Println("Error sending ping message:", err)
				return
			}

		default:
			messageType, message, err := conn.ReadMessage()

			if err != nil {
				log.Println("Error reading message:", err)
				return
			}

			if messageType == websocket.TextMessage && string(message) == "close" {
				fmt.Println("Received 'close' signal from server, ending connection.")
				return
			}

			var parsedMessage map[string]interface{}

			if err := json.Unmarshal(message, &parsedMessage); err != nil {
				fmt.Println("Received message:", string(message))
				log.Println("Error parsing received message:", err)
				continue
			}

			event, ok := parsedMessage["event"].(string)

			if !ok {
				log.Println("Missing or invalid 'event' field:", parsedMessage)
				continue
			}

			data := parsedMessage["data"]

			switch event {
			case "info":
				if message, exists := parsedMessage["message"].(string); exists {
					log.Println("Info:", message)
				} else {
					fmt.Println("Missing or invalid 'message' field in 'info' event data")
				}

			case "error":
				if data != nil {
					log.Println("Error:", data)
				}

			case "send_gcode":
				if data != nil {
					payload, ok := data.(map[string]interface{})
					if ok {
						printerID, pidOk := payload["printerid"].(string)
						gcode, gcodeOk := payload["gcode"].(string)

						if pidOk && gcodeOk {
							response := CommandHandler(gcode, printer)

							fmt.Println("Gcode executed:", response)

							printerResponse := map[string]interface{}{
								"printerid": printerID,
								"response":  response,
							}

							responseMessage, err := json.Marshal(printerResponse)

							if err != nil {
								log.Println("Failed to marshal printer_response:", err)
								continue
							}

							if err := conn.WriteMessage(websocket.TextMessage, responseMessage); err != nil {
								log.Println("Error sending printer_response:", err)
								continue
							}
						} else {
							log.Println("Invalid send_gcode payload")
						}
					} else {
						log.Println("Received G-code command, but data is not a map")
					}
				} else {
					log.Println("Received G-code command, but no data")
				}
			case "printer_connect":
				RegisterPrinter(conn, printer)
			case "printer_disconnect":
				log.Println("Received printer disconnect. Closing connection...")

				conn.Close()
			case "fake_serial_port":
				pid := printer.GetData("productId")

				if pid == nil {
					log.Println("PID not found for this printer!")
					return
				}

				vid := printer.GetAttribute("vendorId")

				if vid == nil {
					log.Println("VID not found for this printer!")
					return
				}

				port := printer.GetData("port")

				if port == nil {
					log.Println("Port not found for this printer!")
					return
				}

				hwid := printer.GetHwid()

				if hwid == "" {
					log.Println("HWID not found for this printer!")
					return
				}

				dataMap := map[string]interface{}{
					"productId": pid,
					"vendorId":  vid,
					"port":      port,
					"hwid":      hwid,
				}

				message := map[string]interface{}{
					"event": "printer_connect",
					"data":  dataMap,
				}

				jsonMessage, err := json.Marshal(message)

				if err != nil {
					log.Println("Failed to marshal printer object:", err)
					return
				}

				log.Println("Sending fake serial port message...")

				conn.WriteMessage(websocket.TextMessage, []byte(jsonMessage))
			default:
				log.Println("Received from server:", string(message))
			}
		}
	}
}

func RegisterPrinter(conn *websocket.Conn, printer *Printer) {
	message := map[string]interface{}{
		"event": "printer_connect",
		"data":  printer,
	}

	jsonMessage, err := json.Marshal(message)

	if err != nil {
		log.Println("Failed to marshal printer object:", err)
		return
	}

	log.Println("Registering printer...")

	conn.WriteMessage(websocket.TextMessage, []byte(jsonMessage))
}

// Run function for G-code command input and processing
func RunCommand(extruder *Extruder, printer *Printer) {
	scanner := bufio.NewScanner(os.Stdin)

	fmt.Println("Enter G-code commands (type 'exit' or 'quit' to quit):")

	for {
		fmt.Print("> ")
		scanner.Scan()
		command := scanner.Text()

		if strings.ToLower(command) == "exit" || strings.ToLower(command) == "quit" {
			fmt.Println("Exiting printer emulator...")
			break
		}

		response := CommandHandler(command, printer)
		fmt.Println(response)
	}

	if err := scanner.Err(); err != nil {
		log.Println("Error reading input:", err)
	}
}
