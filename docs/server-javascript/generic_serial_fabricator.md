# Architecture of GenericSerialFabricator

G-Code instruction queue (Contains `InstructionExtractor` objects)

G-Code extractor queue (Contains `ResponseExtractor` objects)

The processing loop is only started when a fabricator sends data to a serial port. For some fabricators, when we connect to them, they will send some sort of `we're starting up` response which will start the loop. But, other fabricators may not do that. In this case, we send a dummy instruction to start the loop.

During the processing loop, `ResponseExtractor`'s will scan the output from the serial port until they match a regular expression. When they match, the capture groups from the regular expression are passed to a callback function. Then, that callback function will process the results from the capture groups. Usually, the callback function is a reference to a promise's resolve function. In this scenario, the results from the capture groups are returned by the promise. Of course, the callback function can be anything. After all of the response extractors have scanned the output, the output is scanned to see if it contains the `GCODE_PROCESSED_RESPONSE` string. If it contains this, then the next G-Code instruction is sent to the fabricator, else, no G-Code instruction will be sent to the fabricator. At the end of this loop, any data the fabricator sent that was incomplete, is stored in a buffer. Then, this buffer is used as the start of the fabricators output for the next loop.

# Original rough draft for reference:
```py
'data' event received
    append the chunk of data to a string called buffer

    if there is data in the extractor queue
        for each line in the buffer
            for each extractor
                check to see if there is a match for the current line

                if there is a match, call the extractors resolve callback function


    if we receive 'ok\n' (G-Code processed signal)
        if there is data in the instruction queue
            write instruction to serial port

    After everything has completed, all other data in the buffer can be discarded, but because the last line in the buffer could be incomplete, we must save it. Therefore, the new buffer will start with that line
```