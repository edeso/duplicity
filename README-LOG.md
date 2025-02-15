# duplicity's Log Output

Duplicity's log output is meant as a means of reporting status and information 
back to the caller.  This makes the life of a frontend writer much easier.

The format consists of a stream of stanzas, each starting with a keyword and 
some arguments, an optional suggested user text (each line of which starts with 
". ") and ending with an endline.  Like so:

```
KEYWORD 3\n  
. Hello!  All work and now play make Jack a...\n  
. dull boy.\n  
\n  
```

You can get this output by specifying either *--log-fd* or *--log-file*.

Currently, duplicity writes out status messages like WARNING or ERROR followed 
by a message number.  Each message number uniquely identifies a particular 
warning or error so the frontend can take special action.  For example, an ERROR 
of 2 is a command line syntax error.  Each message type has its own namespace 
(i.e. a WARNING of 2 means something different than an ERROR of 2).  A number 
of 1 is a generic, non-unique number for messages without their own code.

For a list of current numbers, see log.py

## HINTS FOR CONSUMERS

1. Ignore any extra arguments on the keyword line.
2. Ignore any stanzas that have a keyword you don't recognize.
3. Ignore any lines in a stanza that start with a character you don't know.

