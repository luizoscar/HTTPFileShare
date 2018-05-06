# HTTPFileShare

HTTPFileShare is a simple Python script to quickly serve files over the Intranet.  
Once the transfer is completed, the server will automatically close.  
If the source is a directory, it will compress the files with the specified archiver (default is tar.gz file).  

**Note:**  
This script is supposed to be compatible with Python 2 and 3.  

## Usage:
```sh
HttpFileShare.py -f [File / Directory] (optional parameters)
```

**Tip for linux users:**  
You can configure an alias, to quickly share the files, by adding to the end of your `~/.bashrc` file the following line:
```sh
alias share='python <path to the HttpFileShare.py> -f'
```
This way, you can call the script simply by typing:
```sh
$ share <My file or Dir>
```
## Mandatory parameter:
**-f [File / Directory]**  
This is the only required parameter, it allow the user to set the file or directory that will be shared.   
If a directory is specified, the files will be compressed before the transfer.  

## Optional parameters:

**-p [TCP Server Port]**     
This allow the user to set the HTTP server TCP port.  
The default port used is 8000.  
**Note:**  For ports lower then 1024, root access will be required.

**-d [Max Downloads]**  
This allow the user to change the max number of downloads before closing the application.  
The default value is to allow 1 download before closing the application.  
**Note:**  For unlimited downloads, set the max downloads value to 0.

**-c [Archiver]**  
If the 'From' parameter is a directory, it will be compressed to a single file before the transfer.  
The script supports the following archives:

| Name | Archiver      | Notes                                                                                      |  
|------|---------------|--------------------------------------------------------------------------------------------|
| gz   | tar.gz file   | This is the default archiver, recommended to share for linux users                         |  
| tar  | tar file      | This is only an archiver, it's the fastest but it will not compress the files       |
| zip  | zip file      | This will compress the file to the popular zip format, recommended to share for windows users      |
| bzip2| tar.bz2 file  | This one will compress more than the gz archiver, but is slower.                                    |
| lzma | tar.xz file   | This should give the best compression, but it is the slowest and it's only available for python > 3.3|
