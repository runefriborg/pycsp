#ifndef __MANDELBROT_KERNEL__H__
#define __MANDELBROT_KERNEL__H__

typedef unsigned short uint16;

void compute(uint16 *u, double h_step, double w_step, double h_start, double w_start, int h, int w, int maxint); 
int iterate_point(double x0, double y0, int max_iterations); 


#endif
