# UAV Track Write-up

## UAV-H1: Dead Reckoning

### 1. What I tried first, and why it did not work
I first considered plotting the GPS fixes on a map to see when the flight path started looking suspicious. I quickly realized this wouldn't work because the spoofing attack was specifically designed to be subtle and smooth; the fake GPS slowly drifted the drone without any obvious jumps, so looking at a map alone wouldn't tell me exactly when the attack started.

### 2. The insight that actually cracked it
I realized that while GPS can be spoofed remotely, the drone's internal IMU (gyros and accelerometers) relies on physical momentum and cannot be faked. I wrote a script using SciPy to numerically integrate the IMU's raw acceleration data over time to calculate the drone's true physical velocity. After detrending the IMU data to fix the sensor drift, I subtracted the true IMU velocity from the fake GPS velocity. The difference stayed completely flat at zero, until a specific timestamp where it violently ramped up, proving exactly when the spoofing began. I then used basic trigonometry (`atan2`) on the final offset values to find the exact compass bearing.

### 3. How I satisfied myself the answer was right
When I graphed the difference between the IMU and the GPS, the result wasn't just messy noise. It was a perfectly flat horizontal line that cleanly broke into a steep ramp exactly at the calculated timestamp. That mathematically perfect shape proved beyond a doubt that I had isolated the artificial spoofing vector.

### 4. Where I used an AI assistant and what I had to correct
While I knew I needed to integrate the acceleration, I had never dealt with raw hardware sensor drift before. I asked an AI why my integrated velocity was flying off into infinity, and it taught me about IMU bias and "detrending." The AI showed me how to use `np.polyfit` on the early "safe" part of the flight to calculate the drift slope and subtract it. It worked perfectly.

---

## UAV-H2: Hopscotch 2

### 1. What I tried first, and why it did not work
My first thought was to reverse the math of the LFSR based on the partial channel log. I considered setting up a system of algebraic equations to solve for the seed, but I realized this would fail instantly. The provided log was extremely messy—full of noise, false detections, and missing channels—meaning any strict equation I built would break immediately.

### 2. The insight that actually cracked it
I realized that a 20-bit LFSR only has 1,048,576 possible starting states. Instead of doing complicated algebra, I could just brute-force it! I wrote a script to generate the channel sequence for every single possible 20-bit seed. For each seed, I checked how many of its predicted channels matched the timestamps in the messy log. The correct seed simply produced a sequence that had a massive overlap with the log, completely bypassing the noise problem.

### 3. How I satisfied myself the answer was right
When I ran the brute-force script, almost every single seed only matched the log 5 or 6 times by random chance. But exactly one seed suddenly matched the log over 30 times. That massive spike in accuracy made it mathematically impossible to be a coincidence, proving I had found the exact secret seed.

### 4. Where I used an AI assistant and what I had to correct
I used an AI to write the core `lfsr_step` function. Implementing the XOR taps for a Fibonacci LFSR in Python requires specific bitwise operations that can be easy to mess up. I gave the AI the tap indices from the challenge description, and it gave me a very fast, optimized bit-shift function. I wrote the brute-force search loop myself.

---

## UAV-H3: Consensus

### 1. What I tried first, and why it did not work
I knew I couldn't just plug all 6 sensor timestamps into a standard Time Difference of Arrival (TDOA) solver. Standard TDOA math completely breaks if even one sensor gives bad data, and the prompt explicitly stated that exactly 2 of the sensors were compromised and lying. A naive approach would just spit out coordinates miles away from the port.

### 2. The insight that actually cracked it
I realized I had to figure out which 4 sensors were telling the truth. Since 4 out of 6 is exactly 15 possible combinations, I wrote a script to test all 15 subsets. For each group of 4, I ran a Nelder-Mead optimizer to find the drone coordinates that had the smallest possible TDOA error. 14 of the groups contained at least one lying sensor, so their error was massive. But exactly one group had a near-zero error. That gave me the true coordinates, and the 2 sensors left out of that group were the liars.

### 3. How I satisfied myself the answer was right
The proof was in the error function. For the wrong groups, the optimizer couldn't get the error below several thousand meters. For the correct group of 4, the error plunged all the way down to nearly 0.0001. That mathematical "cliff" proved that those 4 sensors perfectly agreed with the laws of physics, making my answer undisputable.

### 4. Where I used an AI assistant and what I had to correct
I had never even heard of the Nelder-Mead algorithm or error minimization before this challenge. When I realized I needed to test the combinations of sensors, I asked an AI how to programmatically find the exact coordinates from the messy TDOA data. The AI taught me about objective functions and showed me how to use `scipy.optimize.minimize` to let the Nelder-Mead algorithm lock onto the location for me. I just had to plug my distance calculations into the objective format it provided.
