#!/bin/bash
# Generate RSA key pair for JWT RS256 signing
# Usage: ./generate-jwt-keys.sh [output_directory]
# Output: jwt-private.pem, jwt-public.pem

set -euo pipefail

OUTPUT_DIR="${1:-./jwt-keys}"
KEY_SIZE=2048

echo "Generating JWT RSA key pair..."
echo "Output directory: $OUTPUT_DIR"
echo "Key size: $KEY_SIZE bits"
echo ""

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Generate private key
echo "Generating private key..."
openssl genrsa -out "$OUTPUT_DIR/jwt-private.pem" $KEY_SIZE

# Generate public key from private key
echo "Generating public key..."
openssl rsa -in "$OUTPUT_DIR/jwt-private.pem" -pubout -out "$OUTPUT_DIR/jwt-public.pem"

# Set secure permissions
echo "Setting secure permissions..."
chmod 600 "$OUTPUT_DIR/jwt-private.pem"
chmod 644 "$OUTPUT_DIR/jwt-public.pem"

echo ""
echo "✓ JWT keys generated successfully!"
echo ""
echo "Private key: $OUTPUT_DIR/jwt-private.pem (keep secure - never commit)"
echo "Public key:  $OUTPUT_DIR/jwt-public.pem (can be distributed to services that verify tokens)"
echo ""
echo "Next steps:"
echo "  1. For Kubernetes: kubectl create secret generic jwt-keys \\"
echo "       --from-file=jwt-private.pem=$OUTPUT_DIR/jwt-private.pem \\"
echo "       --from-file=jwt-public.pem=$OUTPUT_DIR/jwt-public.pem"
echo "  2. Mount to /secrets/ in your pod spec"
echo "  3. Set JWT_PRIVATE_KEY_PATH=/secrets/jwt-private.pem"
echo "  4. Set JWT_PUBLIC_KEY_PATH=/secrets/jwt-public.pem"
