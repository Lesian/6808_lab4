Example:
    python trace_generator.py -m trace_generator_map.xml -o output/

Usage:
    -m  Input OSM Map (XML)
    -i  Interpolation Interval (meters)
    -o  Output Folder
    -n  Number of Output Trips
    -g  GPS Noise in Meters (Variance in Gaussian Distribution)

    -v  Enable Visualization


More Example:
    python trace_generator.py -m trace_generator_map.xml -o output/ -n 1000 -g 4.5 -i 20

    With -v, we save the visualization result of this in 1000trips.png and 1000trips_zoomin.png
