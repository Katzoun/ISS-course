/* big iir_online - demo of a simple IIR filter */
/* Honza Cernocky for ISS, 2015 */
/* max length is 1M samples */
/* no error checking, this is an exercise in signal processing, not in programming */
#include <stdio.h>
#include <stdint.h>
#define MAXN  1000000

/* filter coefficients */
int P = 6, Q = 6; 
float A[7] = {     1.000000000000000,  -2.099439053163407,   3.609709467904307,  -3.636253874016913,   3.154538638938833,  -1.538016615547207,   0.622409459323563 }; 

double B[7] = {    0.092255013283721,  -0.120758083660268,   0.064790399505910,  -0.000000000000000,  -0.064790399505910,   0.120758083660268,  -0.092255013283721 }; 

FILE *ifile, *ofile; 
int16_t x[MAXN], y[MAXN];
uint32_t N,n,k;

/* this is the super-difficult filtering function */
float filter (float xn) {
  static double Bmem[8] = {0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0 }; 
  static double Amem[8] = {0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0 }; 
  double yn;
  int k; 
 
  /* vynulovani sumy pro novy vystupni vzorek */ 
  yn = 0.0;

  /* ulozeni noveho vzorku */
  Bmem[0] = xn; 

  /* nejprve vstupni cast - vynasobit, secitat, posunout */
  for (k = Q; k >= 0; k--) {
    yn += Bmem[k] * B[k];
    Bmem[k+1] = Bmem[k];
  }
  /* ted vystupni cast - jedeme jen do 1 !!! */
  for (k = P; k >= 1; k--) {
    yn -= Amem[k] * A[k];
    Amem[k+1] = Amem[k];
  }
  /* vystup je ok, ted ho jeste 'uz zpozdeny' zapamatovat pro pristi beh: */
  Amem[1] = yn;
  /* a na vystup s nim */
  return yn;
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

