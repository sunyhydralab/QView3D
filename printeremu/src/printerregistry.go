package src

import (
	"encoding/json"
	"fmt"
	"io"
	"os"
)

type PrinterConfig struct {
	Id    int          `json:"id"`
	Name  string       `json:"name"`
	Brand PrinterBrand `json:"brand"`
}

type PrinterBrand struct {
	PrinterName  string `json:"printername"`
	PrinterModel string `json:"printermodel"`
}

// LoadPrinters loads a list of printers from the specified JSON file
func LoadPrinters(filePath string) ([]PrinterConfig, error) {
	file, err := os.Open(filePath)

	if err != nil {
		return nil, fmt.Errorf("failed to open file %s: %v", filePath, err)
	}

	defer file.Close()

	fileBytes, err := io.ReadAll(file)

	if err != nil {
		return nil, fmt.Errorf("failed to read file: %v", err)
	}

	var printers []PrinterConfig
	err = json.Unmarshal(fileBytes, &printers)

	if err != nil {
		return nil, fmt.Errorf("failed to unmarshal JSON data: %v", err)
	}

	return printers, nil
}

func PrintPrinters(printers []PrinterConfig) {
	fmt.Println("Loaded printers:")

	for _, printer := range printers {
		fmt.Printf("Printer ID: %d, Name: %s, Brand: %s, Model: %s\n",
			printer.Id, printer.Name, printer.Brand.PrinterName, printer.Brand.PrinterModel)
	}
}
