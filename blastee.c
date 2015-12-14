#include<stdio.h> 
#include<string.h> 
#include<stdlib.h> 
#include<arpa/inet.h>
#include<sys/socket.h>
#include<unistd.h>
#include<sys/time.h>
 
#define BUFLEN 50000  //Max length of buffer
#define MSG_HEADER_LEN 24
#define PORT 8888   //The port on which to listen for incoming data
#define MAX_PACKET_SIZE 500024

struct header {
    char packet_type;
    uint32_t seq_num;
    uint32_t packet_len;
    char *payload;
};

void dump_packet(struct header *pkt) 
{
    /*if(pkt->packet_type == 'E') {
        printf("\nSummary Report: ");
    }*/
    printf("\nPkt_Type %c  Sequence Number: %d Packet Len %d Payload:",
           pkt->packet_type, ntohl(pkt->seq_num), ntohl(pkt->packet_len));
}

float timedifference_msec(struct timeval t0, struct timeval t1)
{
    return (t1.tv_sec - t0.tv_sec) * 1000.0f + (t1.tv_usec - t0.tv_usec) / 1000.0f;
}

void print_summary(struct timeval start_time, int packet_count, int bytes_count) 
{
    struct timeval stop_time;
    float elapsed;
    float calc_elapsed;

    gettimeofday(&stop_time, NULL);
    printf("\nEnd Time %lu:%lu (sec). \n",(stop_time.tv_sec)%100, stop_time.tv_usec/1000);
    
    elapsed = timedifference_msec(start_time, stop_time);
    calc_elapsed = elapsed/1000;

    printf("Summary:\nTotal Packets Recv'd %d \nTotal Bytes Recv'd %d, \nAvg Pkt/sec: %f \nBytes/sec: %f"
           ,packet_count, bytes_count, (packet_count/calc_elapsed), (bytes_count/calc_elapsed));
           
    printf("\nDuration %f (millisec)\n",elapsed);
}

void die(char *s)
{
    perror(s);
    exit(1);
}
 
int main(int argc, char *argv[])
{
    struct sockaddr_in si_me, si_other;
    int s, i, slen = sizeof(si_other) , recv_len;
    //char buf[BUFLEN];
    //char packet[MSG_HEADER_LEN];
    char packet[MAX_PACKET_SIZE];
    int exp_payload_size = 0, recv_payload_size = 0;
    int seqNo = 0;
    int c, sPort = 0, sEcho = 0;
    int packet_count=0, bytes_count=0, duration = 0;
    int global_packet_count = 0, global_bytes_count = 0;
    //char payload[MAX_PACKET_SIZE] = {'\0'};
    //char *payload_ptr;
    struct timeval stop_time, server_start_time, start_time, current_time;
    struct timeval timeout;      
    timeout.tv_sec = 5;  /* A 5 sec timeout */
    
    //Get the Command Line Arguments
    while((c = getopt(argc, argv, "p:c:")) != -1) {
        switch(c) {
            case 'p':
                sPort = atoi(optarg);
                break;
            case 'c':
                sEcho = atoi(optarg);
                break;
            default: /* '?' */
                fprintf(stderr, "Usage: %s -p <port> -c <echo>\n", argv[0]);
                exit(1);
        }
    }

    /* create a UDP socket */
    if ((s=socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)) == -1)
    {
        printf("Error: Could not create socket.");
        die("socket");
    }
    
    printf("Listening on Port: %d\n",sPort);

    // zero out the structure
    memset((char *) &si_me, 0, sizeof(si_me));
     
    si_me.sin_family = AF_INET;
    si_me.sin_port = htons(sPort);
    si_me.sin_addr.s_addr = htonl(INADDR_ANY);
     
    //bind socket to port
    if(bind(s, (struct sockaddr*)&si_me, sizeof(si_me) ) == -1)
    {
        printf("Error: Could not bind socket");
        die("bind");
    }
    
    if (setsockopt (s, SOL_SOCKET, SO_RCVTIMEO, (char *)&timeout,
                        sizeof(timeout)) < 0) {
        die("setsockopt failed");
    }

    //keep listening for data
    while(1)
    {
        //printf("Waiting for data...");
        printf("\n");
        fflush(stdout);

        if(global_packet_count == 0) {
            gettimeofday(&server_start_time, NULL);
            printf("Blastee Start Time %lu:%lu (sec). \n",(server_start_time.tv_sec)%100, server_start_time.tv_usec/1000);
        }

        //try to receive some data, this is a blocking call
        // Clear the buffer.
        memset(packet, 0, sizeof(MAX_PACKET_SIZE));

        /* Recv the packet */
        if ((recv_len = recvfrom(s, packet, MAX_PACKET_SIZE, 0, (struct sockaddr *)&si_other, &slen)) == -1)
        {
            printf("\nFinal Summary: ");
            print_summary(server_start_time, global_packet_count, global_bytes_count);
            die("recvfrom()");
        }
         
        /* Get the current time for this packet */
        gettimeofday(&current_time, NULL);

        /* Keep the counts */
        global_packet_count++;
        packet_count++;
        bytes_count += recv_len;
        global_bytes_count += recv_len;

        if(packet_count == 1) {
            start_time = current_time;  /* On Recving 1st paket start start time. */
            printf("1st Interaction: Start Time %lu:%lu (sec). \n",(start_time.tv_sec)%100, start_time.tv_usec/1000);
        }
        
        struct header* pkt;
        pkt = malloc(sizeof(struct header));
        pkt->payload = malloc(sizeof(recv_len));
        
        pkt = (struct header *)packet;
        pkt->payload = ((struct header *)packet)->payload;
        
        dump_packet(pkt);

        //Crash here
        //printf("Data %s ",*(pkt->payload));
       
        if(pkt->packet_type == 'D') {
            exp_payload_size = ntohl(pkt->packet_len);
            seqNo = ntohl(pkt->seq_num);
        
            printf("\nReceived packet from %s:%d of Size:%d (Bytes) seq no: %d  at time:%lu:%lu(sec) with Payload Size: %d \n",
                inet_ntoa(si_other.sin_addr), ntohs(si_other.sin_port), recv_len, seqNo, (current_time.tv_sec)%100, current_time.tv_usec/1000, exp_payload_size);
       
            //printf(" Data: %s\n",packet);
        }
        
        if(pkt->packet_type == 'E') {
            printf("\nRecv'd End packet: ");
            print_summary(start_time, packet_count, bytes_count);
        
            /* Reinitailze the values */ 
            packet_count = 0;
            bytes_count = 0;
        }
 
        /*now reply the client with the same data
        if (sendto(s, buf, recv_len, 0, (struct sockaddr*) &si_other, slen) == -1)
        {
            die("sendto()");
        }
            */
        //free(pkt->payload);
        //free(pkt);

    }
 
    close(s);
    return 0;
}
