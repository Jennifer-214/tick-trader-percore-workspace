// Disposable runtime-confirm harness (F-056/F-057): compare FPN_Sqrt<64> raw bytes
// built WITH vs WITHOUT USE_NATIVE_128. If outputs differ, production (native, sqrt-double)
// diverges from the tested generic Newton-Raphson path. Throwaway — lives only in the clone.
#include "FixedPoint/FixedPointN.hpp"
#include <cstdio>
#include <cstring>
#include <cstdint>
using namespace std;

static void dump(const char* tag, double d) {
    FPN<64> x = FPN_FromDouble<64>(d);
    FPN<64> r = FPN_Sqrt<64>(x);
    unsigned char b[sizeof(FPN<64>)];
    memcpy(b, &r, sizeof(r));
    printf("%s sqrt(%.10g) [%zuB]:", tag, d, sizeof(FPN<64>));
    for (size_t i = 0; i < sizeof(FPN<64>); ++i) printf(" %02x", b[i]);
    printf("  ~= %.17g\n", FPN_ToDouble<64>(r));
}

int main() {
#ifdef USE_NATIVE_128
    const char* tag = "[NATIVE ]";
#else
    const char* tag = "[GENERIC]";
#endif
    double in[] = {2.0, 3.0, 1.5, 0.25, 100.0, 12345.678, 2.0000001, 0.0001, 9999999.0};
    for (size_t i = 0; i < sizeof(in)/sizeof(in[0]); ++i) dump(tag, in[i]);
    return 0;
}
