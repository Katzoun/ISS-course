/* wire -  reads input sound (assumes shorts) and copies to output */
/* Honza Cernocky for ISS, 2015 */
/* max length is 1M samples */
/* no error checking, this is an exercise in signal processing, not in programming */
#include <stdio.h>
#include <stdint.h>
#define MAXN  1000000


FILE *ifile, *ofile; 
int16_t x[MAXN], y[MAXN];
uint32_t N; 

main (int argc, char *argv[]) {
  ifile = fopen(argv[1],"rb"); 
  ofile = fopen(argv[2],"wb"); 

  /* read it */
  N = fread(x, sizeof(int16_t), MAXN, ifile); fclose(ifile); 
  printf ("read %d samples\n", N); 
  /* write it */
  fwrite(x, sizeof(int16_t), N, ofile); fclose(ofile); 
  printf ("written %d samples\n", N); 
}

