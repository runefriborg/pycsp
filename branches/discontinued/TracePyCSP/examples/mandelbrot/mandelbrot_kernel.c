/*
Compile on mac:
gcc -dynamiclib mandelbrot_kernel.c -o mandelbrot_kernel.dylib

Compile on linux:
gcc -shared mandelbrot_kernel.c -o mandelbrot_kernel.so

 */
#include <stdio.h>
#include "mandelbrot_kernel.h"


void compute(uint16 *u, double h_step, double w_step, double h_start, double w_start, int h, int w, int maxint)
{
    int x,y;
    
    if (0) 
        printf("h_step %e, w_step %e, h_start %e, w_start %e, h %d, w %d, maxint %d\n", 
               h_step, w_step, h_start, w_start, h, w, maxint); 
    
    for (y=0; y<h; y++)
    {
        for(x=0; x<w; x++)
        {
            u[y*w+x] = (uint16) 
                iterate_point(w_start + ((double)x) * w_step, 
                              h_start + ((double)y) * h_step, 
                              maxint);
        }
    }
}

int iterate_point(double x0, double y0, int max_iterations)
{
    int iteration = 0;
    double x=x0, y=y0, x2=x*x, y2=y*y;
    
    //printf("%f,%f,%d\n", x0, y0, max_iterations);
    while (x2+y2<4 && iteration<max_iterations) 
    {
        y = 2*x*y + y0;
        x = x2-y2 + x0;
        x2 = x*x;
        y2 = y*y;
        iteration++;
    }
    return iteration;
}

