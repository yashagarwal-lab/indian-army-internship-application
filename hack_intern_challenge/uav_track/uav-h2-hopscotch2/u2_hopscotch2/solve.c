#include <stdio.h>
#include <stdlib.h>
#include <math.h>

#define MASK 0xFFFFF

typedef struct {
    int k;
    int c;
} Detection;

int step(int s) {
    int fb = ((s >> 19) ^ (s >> 16)) & 1;
    return ((s << 1) | fb) & MASK;
}

int channel_of(int s) {
    int t1 = s & 0x7F;
    int t2 = (s >> 7) & 0x7F;
    int t3 = (s >> 14) & 0x3F;
    return ((t1 ^ t2) + (t2 * t3)) % 80;
}

int main() {
    FILE *f = fopen("detections.csv", "r");
    if (!f) {
        printf("Failed to open detections.csv\n");
        return 1;
    }
    
    char line[256];
    fgets(line, sizeof(line), f); // skip header
    
    Detection detections[1000];
    int num_detections = 0;
    
    while (fgets(line, sizeof(line), f)) {
        double t;
        int c;
        if (sscanf(line, "%lf,%d", &t, &c) == 2) {
            int k = (int)round(t / 0.02);
            detections[num_detections].k = k;
            detections[num_detections].c = c;
            num_detections++;
        }
    }
    fclose(f);
    
    printf("Loaded %d detections.\n", num_detections);
    
    int max_k = 0;
    for (int i = 0; i < num_detections; i++) {
        if (detections[i].k > max_k) {
            max_k = detections[i].k;
        }
    }
    
    // Create an array indicating expected channels at each k
    // Since there can be multiple detections at the same k (noise), 
    // we just store a boolean matrix of valid channels for each k.
    int valid[1005][80] = {0};
    for (int i = 0; i < num_detections; i++) {
        valid[detections[i].k][detections[i].c] = 1;
    }
    
    int best_s0 = -1;
    int best_score = -1;
    
    for (int s0 = 0; s0 <= MASK; s0++) {
        int s = s0;
        int score = 0;
        for (int k = 0; k <= max_k; k++) {
            int c = channel_of(s);
            if (valid[k][c]) {
                score++;
            }
            s = step(s);
        }
        if (score > best_score) {
            best_score = score;
            best_s0 = s0;
        }
    }
    
    printf("Best s0: %d (score: %d)\n", best_s0, best_score);
    
    // Now simulate forward to 1011
    int s = best_s0;
    for (int k = 0; k <= 1011; k++) {
        if (k >= 1000) {
            printf("%d%s", channel_of(s), (k == 1011) ? "" : "-");
        }
        s = step(s);
    }
    printf("\n");
    
    return 0;
}
