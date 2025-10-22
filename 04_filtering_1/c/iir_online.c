/* iir_online - demo of a simple FIR filter */
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

/* this is the super-difficult filtering function */
float filter (float xn) {
  static float xn1 = 0.0, xn2 = 0.0, xn3 = 0.0;  
  static float yn1 = 0.0, yn2 = 0.0, yn3 = 0.0;  
  float yn; 
  /* do the filtering */
  yn = b0 * xn + b1 * xn1 + b2 * xn2 + b3 * xn3
               - a1 * yn1 - a2 * yn2 - a3 * yn3; 
  /* do the shifting - make all samples older ... */
  xn3 = xn2; 
  xn2 = xn1; 
  xn1 = xn; 
  yn3 = yn2; 
  yn2 = yn1; 
  yn1 = yn; 
  return (yn); 
}


main (int argc, char *argv[]) {
  ifile = fopen(argv[1],"rb"); 
  ofile = fopen(argv[2],"wb"); 

  /* read it */
  N = fread(x, sizeof(int16_t), MAXN, ifile); fclose(ifile); 
  printf ("read %d samples\n", N); 

  /* do the filtering */
  for (n=0; n<N; n++) {
    y[n] = filter (x[n]); 
  }

  /* write it */
  fwrite(y, sizeof(int16_t), N, ofile); fclose(ofile); 
  printf ("written %d samples\n", N); 
}

