/* big iir_offline - demo of a simple IIR filter */
/* Honza Cernocky for ISS, 2015 */
/* max length is 1M samples */
/* no error checking, this is an exercise in signal processing, not in programming */
#include <stdio.h>
#include <stdint.h>
#define MAXN  1000000

/* filter coefficients */
int P = 6, Q = 6; 
double A[7] = {     1.000000000000000,  -2.099439053163407,   3.609709467904307,  -3.636253874016913,   3.154538638938833,  -1.538016615547207,   0.622409459323563 }; 

double B[7] = {    0.092255013283721,  -0.120758083660268,   0.064790399505910,  -0.000000000000000,  -0.064790399505910,   0.120758083660268,  -0.092255013283721 }; 

FILE *ifile, *ofile; 
int16_t x[MAXN], y[MAXN];
uint32_t N,n,k;
double sum;  

main (int argc, char *argv[]) {
  ifile = fopen(argv[1],"rb"); 
  ofile = fopen(argv[2],"wb"); 

  /* read it */
  N = fread(x, sizeof(int16_t), MAXN, ifile); fclose(ifile); 
  printf ("read %d samples\n", N); 

  /* the filtering is here */
  for (n=P; n<N; n++) {  
    sum = 0.0;  /* zero the accumulator */
    for (k=0; k<=Q; k++) { /* non-recursive part first */
      sum += B[k] * x[n-k]; 
    }
    for (k=1; k<=P; k++) { /* recursive part, attention to 1 ! */
      sum -= A[k] * y[n-k]; 
    }
    y[n] = (int16_t)sum; 
  }

  /* write it */
  fwrite(y, sizeof(int16_t), N, ofile); fclose(ofile); 
  printf ("written %d samples\n", N); 
}

