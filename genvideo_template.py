__gdl90_master_path__ = "path-to-gdl90-master-lib"

import sys
sys.path.append(__gdl90_master_path__)
print(sys.path)

from simulate_GarminFromFile import simulateIt


if __name__ == '__main__':
    simulateIt("example.csv", takeoff_altitude=1350, landing_altitude=1321, timeofstart=180, callSign="DETGZ")

