# UAV Track Writeup

### UAV-H1: Dead Reckoning

**Goal:**
A drone's GPS was spoofed to slowly push it off course. I was given the spoofed GPS fixes and the raw acceleration data from the drone's internal IMU. My goal was to find the exact time the spoofing started and what compass direction it was pushing the drone.

**Thought process:**
The GPS can be spoofed, but the internal IMU measures real physical acceleration, which can't be faked remotely. I knew from physics that if I integrate acceleration over time, I get velocity. 

I wrote a script to numerically integrate the IMU acceleration to find the drone's true velocity. The IMU had a slight uncalibrated drift, so I detrended the data based on the clean early part of the flight. Then, I just subtracted the true IMU velocity from the spoofed GPS velocity. The difference stayed at a flat zero until the spoofing started, and then it ramped up to a flat plateau. I just looked at the graph to find the start time, and used the `atan2` math function on the plateau values to find the exact compass bearing.

**What I learned:**
This challenge was really cool because it showed me how integrating raw physics sensors can completely expose fake GPS data.

***

### UAV-H2: Hopscotch 2

**Goal:**
A radio was hopping channels using a 20-bit Fibonacci LFSR. I was given a messy, incomplete log of some of its channel hops. My goal was to figure out the secret initial 20-bit seed and predict the next 12 channels.

**Thought process:**
Usually, cryptographic keys are huge, but a 20-bit LFSR only has about a million possible initial states. That is extremely small for a computer, meaning I didn't need to do any crazy math—I could just brute-force it.

I wrote a fast script to test every single one of the 1,048,576 possible seeds. For each seed, I simulated the LFSR forward to generate the channel sequence and compared it against the timestamps in the messy log. Even though the log had noise and missing data, the correct seed was obvious because its predicted channels matched the log perfectly. Once I had the seed, I just ran the LFSR 1000 steps forward to print the flag.

**What I learned:**
This challenge was really cool because it showed me that you don't always need clever math if the state space is small enough to just brute-force.

***

### UAV-H3: Consensus

**Goal:**
Six sensors reported the arrival times of radio bursts from a hovering drone to locate it. However, exactly two sensors were compromised and lying. My goal was to find the true location of the drone and identify the two lying sensors.

**Thought process:**
This is a standard Time Difference of Arrival (TDOA) problem. If I know the drone's position, the time difference between sensors is strictly defined by the speed of light. Since 2 sensors were lying, 4 sensors were telling the truth.

There are exactly 15 different ways to pick 4 sensors out of 6. I wrote a script that tested all 15 combinations. For each combination, I ran an optimizer to find the drone coordinates that had the smallest TDOA error. 14 combinations had massive errors because they included a lying sensor, but exactly one combination snapped to a near-zero error. That gave me the true coordinates, and the two left-out sensors were the liars.

**What I learned:**
This challenge was really cool because it showed me how to use combinatorics and error minimization to filter out bad sensor data.
