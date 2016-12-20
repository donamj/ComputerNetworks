# Importing relevant modules
import socket
import sys
import thread
import logging
import time
import requests

# To log all the events to log.txt
logging.basicConfig(filename="log.txt",level=logging.INFO,format='%(asctime)s : %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

#Thread created for each connection
#The method creates cache, fetch data from cache or servre as per the availability
def connection_thread(msg, clientSocket):
    #To get the connection start time
    time_start = time.time()

    requestType = msg[0] #Method, here it will be GET
    requestUrl = msg[1]
    requestUrl = requestUrl[1:] #The requested URL
    print "Request : ", requestType
    print "URL : ", requestUrl
    #Logging the info
    logging.info("Request : "+ str(requestType))
    logging.info("URL : "+str(requestUrl))

    cntr = 1
    # Printing the server details
    print "CLIENT SOCKET DETAILS:"
    logging.info("CLIENT SOCKET DETAILS:")
    for responses in socket.getaddrinfo(socket.gethostname(), 'http'):
        family, socktype, proto, canonname, sockaddr = responses
        if cntr == 1:
            print 'Family        -', families[family]
            logging.info("\n Family - " + families[family])
            print 'Type          -', types[socktype]
            logging.info("\n Type - " + types[socktype])
            print 'Protocol      -', protocols[proto]
            logging.info("\n Protocol - " + protocols[proto])
            cntr = cntr + 1

    try:
        # Check whether the file exists in the cache
        file = open(requestUrl, "r")
        data = file.readlines()
        print "File available in cache...\n"
        logging.info("File available in cache\n")
        print "File retrieved from cache\n"
        logging.info("File retrieved from cache\n")

        # Getting the cached file content
        for i in range(0, len(data)):
            #print (data[i])
            logging.info(str(data[i]))
            #Sending the data through the client socket
            clientSocket.send(data[i])

        #Logging the response send
        print "Response length : ",len(data)," bytes"
        logging.info("Response length : "+ str(len(data))+" bytes")

        # Noting the end time to calculate RTT
        time_end = time.time()
        rtt = time_end - time_start
        print 'RTT for cached file : ', rtt,' secs'
        logging.info("RTT for cached file : " + str(rtt) + ' secs')

    #Handles the process when the file is not cached already
    #Fetches the file from server
    except IOError:
        print "Could not find file in cache..."
        print "Retreving file from server..."
        logging.info("Could not find file in cache...")
        logging.info("Retreving file from server...")

        #Creating a proxy server socket
        proxyServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Printing the proxy server details
        cntr = 1
        print "PROXY SERVER SOCKET DETAILS:"
        logging.info("PROXY SERVER SOCKET DETAILS:")
        for responses in socket.getaddrinfo(socket.gethostname(), 'http'):
            family, socktype, proto, canonname, sockaddr = responses
            if cntr == 1:
                print 'Family        - ', families[family]
                logging.info("\n Family - " + families[family])
                print 'Type          - ', types[socktype]
                logging.info("\n Type - " + types[socktype])
                print 'Protocol      - ', protocols[proto]
                logging.info("\n Protocol - " + protocols[proto])
                print "Host Name    - ", requestUrl
                logging.info("Host Name     - " + str(requestUrl))
                cntr = cntr + 1

        try:
            #Fetching data from real server
            proxyServer.connect((requestUrl, 80))
            print 'Socket connected to host at port 80'
            logging.info('Socket connected to host at port 80')
            # Request to be send
            request = b"GET / HTTP/1.1\nHost: " + requestUrl + "\n\n"
            logging.info("Reuest to web server : GET / HTTP/1.1\nHost: " + requestUrl + "\n\n")
            # Sending request web server
            proxyServer.send(request)
            # Receive response from actual web server
            response = proxyServer.recv(10000)
            # Logging the response header received from  actual web server
            url = "http://" + requestUrl
            responseHeader = requests.head(url)
            logging.info("Reponse header : "+str(responseHeader.headers))
            print "Length of response from web server to proxy : "+str(len(response)) + " bytes"
            logging.info("Length of response from web server to proxy : "+str(len(response)) + " bytes")

            #Caching the response obtained from the web server
            cacheFile = open(requestUrl, "wb")
            cacheFile.write(response)
            cacheFile.close()
            print "Caching Done!!! "
            logging.info("Caching Done!!! ")

            # Noting the end time to calculate RTT
            time_end = time.time()
            rtt = time_end - time_start
            print 'RTT for file from web server : ', rtt,
            logging.info("RTT for file from web server : " + str(rtt) + 'secs')

            #Close client socket
            clientSocket.close()
            #Close server socket
            proxyServer.close()

        # Error handling
        except:
            print 'Error: Illegal Request for ',requestUrl,'!!!'
            logging.error('Illegal Request for '+requestUrl+' !!!')

            # Sending error message to client
            clientSocket.send('HTTP/1.1 404 not found\r\n')
            logging.info("HTTP/1.1 404 not found\n")

            time_end = time.time()
            rtt = time_end - time_start
            print 'RTT for error request : ', rtt, ' secs'
            logging.info("RTT for error request : " + str(rtt)+' secs')

    #End of one request
    logging.info("*****************************************************************************************\n\n\n")
    clientSocket.close()    #Closing the socket

# To get the socket properties
# Reference : https://pymotw.com/2/socket/addressing.html
def get_constants(prefix):
    """Create a dictionary mapping socket module constants to their names."""
    return dict((getattr(socket, n), n)
                for n in dir(socket)
                if n.startswith(prefix)
                )
families = get_constants('AF_')
types = get_constants('SOCK_')
protocols = get_constants('IPPROTO_')

def main():
    # Error handling when port number is not entered
    if len(sys.argv) <= 1:
        print 'Error: Port number expected as argument'
        logging.info('Error: Port number expected as argument')
        print 'Default port 8080 used.'
        logging.info('Default port 8080 used.')
        portNo = 8080
    else:
        # Assigning port number given by the user
        portNo = int(sys.argv[1])

    # Creating a server socket
    try:
        serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print "Server socket created...."
        logging.info("Server socket created....")
    # Handling a case when the socket was not created
    except socket.error as err:
        print 'Server Socket not created.\n Error %s' % (err)

    #Binding the socket to given port numbe
    serverSocket.bind(('', portNo))
    #Server listening for connection
    #Here the number of connections that can be queued
    serverSocket.listen(5)
    logging.info("Server host name : " + socket.gethostname())
    logging.info("Host Address : " + socket.gethostbyname(socket.gethostname()) + " \n")
    print ("Server host name : " + socket.gethostname())
    print ("Host Address : " + socket.gethostbyname(socket.gethostname()) + " \n")

    cntr = 1
    #Printing the server details
    print "SERVER SOCKET DETAILS:"
    logging.info("SERVER SOCKET DETAILS:")
    for responses in socket.getaddrinfo(socket.gethostname(), 'http'):
        family, socktype, proto, canonname, sockaddr = responses
        if cntr==1:
            print 'Family        -', families[family]
            logging.info("\n Family - " + families[family])
            print 'Type          -', types[socktype]
            logging.info("\n Type - " + types[socktype])
            print 'Protocol      -', protocols[proto]
            logging.info("\n Protocol - " + protocols[proto])
            cntr = cntr+1

    while 1:
        # Start receiving data from the client
        print 'Waiting for requests...'
        logging.info("Waiting for requests....")

        clientSocket, clientAddress = serverSocket.accept()
        print "Accepting connection\n"
        logging.info("Accepting connection")

        print "Connection received from cache with IP address - ", str(clientAddress[0]), ":", str(clientAddress[1]),'\n'
        logging.info("Connection received from cache with IP address - " + str(clientAddress[0]) + ":" + str(clientAddress[1]))

        #
        message = clientSocket.recv(1024)
        msg = message.split()
        if len(msg) <= 1:
            continue

        #Start a new thread to handle the connection
        thread.start_new_thread(connection_thread,(msg, clientSocket))

if __name__ == "__main__":
    main()