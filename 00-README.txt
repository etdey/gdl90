Sending raw GDL-90 data files to network:

  sudo ncat -u --send-only 10.1.1.13 43211 < skyradar-20180826.raw


Converting raw GDL-90 to text import format for KML plotter:

  ./gdl90_receiver.py -i skyradar.20120912.002 | egrep '^MSG10:' | sed -e 's/^MSG10: /- /' > ../KML/PlotFlight/skyradar.trackxxx.txt


New style with automatic time computations:

  ./gdl90_receiver.py -i skyradar.20121028.001 --plotflight > ../KML/PlotFlight/skyradar.track.20121028.001.txt
