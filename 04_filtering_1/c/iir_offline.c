/* iir_offline - demo of a simple IIR filter */
/* Honza Cernocky for ISS, 2015 */
/* max length is 1M samples */
/* no error checking, this is an exercise in signal processing, not in programming */
#include <stdio.h>
#include <stdint.h>
#define MAXN  1000000

/* filter coefficients */
#define b0 0.25
#define b1 0.25
#define b2 0.25
#define b3 0.25
#define a1 -0.25
#define a2 0.25
#define a3 -0.25


FILE *ifile, *ofile; 
int16_t x[MAXN], y[MAXN];
uint32_t N,n; 

main (int argc, char *argv[]) {
  ifile = fopen(argv[1],"rb"); 
  ofile = fopen(argv[2],"wb"); 

  /* read it */
  N = fread(x, sizeof(int16_t), MAXN, ifile); fclose(ifile); 
  printf ("read %d samples\n", N); 

  /* the filtering is here */
  for (n=3; n<N; n++) {   /* why do we begin from 3 ??? */
    y[n] = b0 * x[n] + b1 * x[n-1] + b2 * x[n-2] + b3 * x[n-3]
                     - a1 * y[n-1] - a2 * y[n-2] - a3 * y[n-3]; 
  }

  /* write it */
  fwrite(y, sizeof(int16_t), N, ofile); fclose(ofile); 
  printf ("written %d samples\n", N); 
}

