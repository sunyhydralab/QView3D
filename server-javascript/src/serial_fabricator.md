# Contains drafts for more complicated code

Architecture for Generic Serial Fabricator

G-Code instruction Queue [Contains Strings] **Still a queue but different data**

G-Code Extractor Queue [Contains Regex Objects] **Still a queue but different data**

'data' event received **Similar layout**
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
    

