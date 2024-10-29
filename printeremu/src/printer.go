package src

import "fmt"

type Printer struct {
	id          int
	device      string
	description string
	hwid        string
	name        string
	status      string
	date        string
	extruder    *Extruder // Keep this as a pointer
}

func NewPrinter(id int, device, description, hwid, name, status, date string, extruder *Extruder) *Printer {
	return &Printer{
		id:          id,
		device:      device,
		description: description,
		hwid:        hwid,
		name:        name,
		status:      status,
		date:        date,
		extruder:    extruder,
	}
}

func (p *Printer) SetExtruderTemp(temp float64) {
	p.extruder.SetExtruderTemp(temp)
}

func (p *Printer) GetExtruderTemp() float64 {
	return p.extruder.ExtruderTemp
}

func (p *Printer) GetExtruder() *Extruder {
	return p.extruder
}

func (p *Printer) String() string {
	return fmt.Sprintf("Printer{Id: %d, Device: %s, Description: %s, Hwid: %s, Name: %s, Status: %s, Date: %s, Extruder: %v}",
		p.id, p.device, p.description, p.hwid, p.name, p.status, p.date, p.extruder.String())
}
