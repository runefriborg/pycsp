from simulation import Now
from pycsp.greenlets.const import *

class Histogram(list):
    """ A histogram gathering and sampling class"""

    def __init__(self, name = '', low = 0.0, high = 100.0, nbins = 10):
        list.__init__(self)
        self.name  = name
        self.low   = float(low)
        self.high  = float(high)
        self.nbins = nbins
        self.binsize = (self.high - self.low) / nbins
        self._nrObs = 0
        self._sum = 0
        self[:] = [[low + (i - 1) * self.binsize, 0] for i in range(self.nbins + 2)]
       
    def addIn(self, y):
        """ add a value into the correct bin"""
        self._nrObs += 1
        self._sum += y
        b = int((y - self.low + self.binsize) / self.binsize)
        if b < 0: b = 0
        if b > self.nbins + 1: b = self.nbins + 1
        assert 0 <= b <=self.nbins + 1, 'Histogram.addIn: b out of range: %s'%b
        self[b][1] += 1
        
    def __str__(self):
        histo = self
        ylab = 'value'
        nrObs = self._nrObs
        width = len(str(nrObs))
        res = []
        res.append(' < Histogram %s:'%self.name)
        res.append('\nNumber of observations: %s'%nrObs)
        if nrObs:
            su = self._sum
            cum = histo[0][1]
            fmt = '%s'
            line = '\n%s <= %s < %s: %s (cum: %s/%s%s)'\
                 %(fmt, '%s', fmt, '%s', '%s', '%5.1f', '%s')
            line1 = '\n%s%s < %s: %s (cum: %s/%s%s)'\
                 %('%s', '%s', fmt, '%s', '%s', '%5.1f', '%s')
            l1width = len(('%s <= '%fmt)%histo[1][0])
            res.append(line1\
                       %(' ' * l1width, ylab, histo[1][0], str(histo[0][1]).rjust(width),\
                         str(cum).rjust(width),(float(cum) / nrObs) * 100, '%')
                      )
            for i in range(1, len(histo) - 1):
                cum += histo[i][1]
                res.append(line\
                       %(histo[i][0], ylab, histo[i + 1][0], str(histo[i][1]).rjust(width),\
                         str(cum).rjust(width),(float(cum) / nrObs) * 100, '%')
                          )
            cum += histo[-1][1]
            linen = '\n%s <= %s %s : %s (cum: %s/%s%s)'\
                  %(fmt, '%s', '%s', '%s', '%s', '%5.1f', '%s')
            lnwidth = len(('<%s'%fmt)%histo[1][0])
            res.append(linen\
                       %(histo[-1][0], ylab, ' ' * lnwidth, str(histo[-1][1]).rjust(width),\
                       str(cum).rjust(width),(float(cum) / nrObs) * 100, '%')
                       )
        res.append('\n > ')
        return ' '.join(res)


class Monitor(list):
    """ Monitored variables

    A Class for monitored variables, that is, variables that allow one
    to gather simple statistics.  A Monitor is a subclass of list and
    list operations can be performed on it. An object is established
    using m = Monitor(name = '..'). It can be given a
    unique name for use in debugging and in tracing and ylab and tlab
    strings for labelling graphs.
    """
    def __init__(self, name = 'a_Monitor', ylab = 'y', tlab = 't'):
        list.__init__(self)
        self.startTime = 0.0
        self.name = name
        self.ylab = ylab
        self.tlab = tlab
        
    def setHistogram(self, name = '', low = 0.0, high = 100.0, nbins = 10):
        """Sets histogram parameters.
        Must be called before call to getHistogram"""
        if name == '':
            histname = self.name
        else:
            histname = name
        self.histo = Histogram(name = histname, low = low, high = high, nbins = nbins)

    def observe(self, y,t = None):
        """record y and t"""
        if t is  None: t = Now()
        self.append([t, y])
        logging.debug("y:%d,time:%d"%(y,t))

    def tally(self, y):
        """ deprecated: tally for backward compatibility"""
        self.observe(y, 0)
                   
    def accum(self, y,t = None):
        """ deprecated:  accum for backward compatibility"""
        self.observe(y, t)

    def reset(self, t = None):
        """reset the sums and counts for the monitored variable """
        self[:] = []
        if t is None: t = Now()
        self.startTime = t
        
    def tseries(self):
        """ the series of measured times"""
        return list(zip(*self)[0])

    def yseries(self):
        """ the series of measured values"""
        return list(zip(*self)[1])

    def count(self):
        """ deprecated: the number of observations made """
        return self.__len__()
        
    def total(self):
        """ the sum of the y"""
        if self.__len__() == 0:  return 0
        else:
            sum = 0.0
            for i in range(self.__len__()):
                sum += self[i][1]
            return sum # replace by sum() later

    def mean(self):
        """ the simple average of the monitored variable"""
        try: return 1.0 * self.total() / self.__len__()
        except:  print 'SimPy: No observations  for mean'

    def var(self):
        """ the sample variance of the monitored variable """
        n = len(self)
        tot = self.total()
        ssq = 0.0
        for i in range(self.__len__()):
            ssq += self[i][1] ** 2 # replace by sum() eventually
        try: return (ssq - float(tot * tot) / n) / n
        except: print 'SimPy: No observations for sample variance'
        
    def timeAverage(self, t = None):
        """ the time - weighted average of the monitored variable.

            If t is used it is assumed to be the current time,
            otherwise t =  self.sim.now()
        """
        N = self.__len__()
        if N  == 0:
            print 'SimPy: No observations for timeAverage'
            return None

        if t is None: t = Now()
        sum = 0.0
        tlast = self[0][0]
        ylast = self[0][1]
        for i in range(N):
            ti, yi = self[i]
            sum += ylast * (ti - tlast)
            tlast = ti
            ylast = yi
        sum += ylast * (t - tlast)
        T = tlast - self[0][0]
        if T == 0:
             print 'SimPy: No elapsed time for timeAverage'
             return None
        return sum / float(T)

    def timeVariance(self, t = None):
        """ the time - weighted Variance of the monitored variable.

            If t is used it is assumed to be the current time,
            otherwise t =  self.sim.now()
        """
        N = self.__len__()
        if N  == 0:
            print 'SimPy: No observations for timeVariance'
            return None
        if t is None: t = Now()
        sm = 0.0
        ssq = 0.0
        tlast = self[0][0]
        # print 'DEBUG: 1 twVar ', t, tlast
        ylast = self[0][1]
        for i in range(N):
            ti, yi = self[i]
            sm  += ylast * (ti - tlast)
            ssq += ylast * ylast * (ti - tlast)
            tlast = ti
            ylast = yi
        sm  += ylast * (t - tlast)
        ssq += ylast * ylast * (t - tlast)
        T = tlast - self[0][0]
        if T == 0:
             print 'SimPy: No elapsed time for timeVariance'
             return None
        mn = sm / float(T)
        return ssq / float(T) - mn * mn


    def histogram(self, low = 0.0, high = 100.0, nbins = 10):
        """ A histogram of the monitored y data values.
        """
        h = Histogram(name = self.name, low = low, high = high, nbins = nbins)
        ys = self.yseries()
        for y in ys: h.addIn(y)
        return h
        
    def getHistogram(self):
        """Returns a histogram based on the parameters provided in
        preceding call to setHistogram.
        """
        ys = self.yseries()
        h = self.histo
        for y in ys: h.addIn(y)
        return h
    
    def printHistogram(self, fmt = '%s'):
        """Returns formatted frequency distribution table string from Monitor.
        Precondition: setHistogram must have been called.
        fmt == format of bin range values
        """
        try:
            histo = self.getHistogram()
        except:
            raise FatalSimerror('histogramTable: call setHistogram first'\
                                ' for Monitor %s'%self.name)            
        ylab = self.ylab
        nrObs = self.count()
        width = len(str(nrObs))
        res = []
        res.append('\nHistogram for %s:'%histo.name)
        res.append('\nNumber of observations: %s'%nrObs)
        su = sum(self.yseries())
        cum = histo[0][1]
        line = '\n%s <= %s < %s: %s (cum: %s/%s%s)'\
             %(fmt, '%s', fmt, '%s', '%s', '%5.1f', '%s')
        line1 = '\n%s%s < %s: %s (cum: %s/%s%s)'\
             %('%s', '%s', fmt, '%s', '%s', '%5.1f', '%s')
        l1width = len(('%s <= '%fmt)%histo[1][0])
        res.append(line1\
                   %(' ' * l1width, ylab, histo[1][0], str(histo[0][1]).rjust(width),\
                     str(cum).rjust(width),(float(cum) / nrObs) * 100, '%')
                  )
        for i in range(1, len(histo) - 1):
            cum += histo[i][1]
            res.append(line\
                   %(histo[i][0], ylab, histo[i + 1][0], str(histo[i][1]).rjust(width),\
                     str(cum).rjust(width),(float(cum) / nrObs) * 100, '%')
                      )
        cum += histo[-1][1]
        linen = '\n%s <= %s %s : %s (cum: %s/%s%s)'\
              %(fmt, '%s', '%s', '%s', '%s', '%5.1f', '%s')
        lnwidth = len(('<%s'%fmt)%histo[1][0])
        res.append(linen\
                   %(histo[-1][0], ylab, ' ' * lnwidth, str(histo[-1][1]).rjust(width),\
                   str(cum).rjust(width),(float(cum) / nrObs) * 100, '%')
                   )
        return ' '.join(res)
        

