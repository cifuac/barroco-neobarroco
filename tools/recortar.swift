// Recorta el sujeto principal de una imagen (reconocimiento de sujetos de macOS / Vision) y guarda un PNG con transparencia.
// Uso: swift tools/recortar.swift <entrada> <salida.png>
import Foundation
import Vision
import CoreImage
import ImageIO
import UniformTypeIdentifiers

let args = CommandLine.arguments
guard args.count >= 3 else { print("uso: recortar <entrada> <salida.png>"); exit(1) }
let entrada = URL(fileURLWithPath: args[1]), salida = URL(fileURLWithPath: args[2])
guard let fuente = CGImageSourceCreateWithURL(entrada as CFURL, nil),
      let cg = CGImageSourceCreateImageAtIndex(fuente, 0, nil) else { print("no se pudo leer"); exit(1) }
let pedido = VNGenerateForegroundInstanceMaskRequest()
let manejador = VNImageRequestHandler(cgImage: cg, options: [:])
do {
  try manejador.perform([pedido])
  guard let r = pedido.results?.first else { print("sin sujeto"); exit(2) }
  let buf = try r.generateMaskedImage(ofInstances: r.allInstances, from: manejador, croppedToInstancesExtent: true)
  let ci = CIImage(cvPixelBuffer: buf)
  let ctx = CIContext()
  guard let out = ctx.createCGImage(ci, from: ci.extent),
        let dest = CGImageDestinationCreateWithURL(salida as CFURL, UTType.png.identifier as CFString, 1, nil) else { exit(3) }
  CGImageDestinationAddImage(dest, out, nil)
  CGImageDestinationFinalize(dest)
  print("ok \(r.allInstances.count) sujeto(s) \(out.width)x\(out.height)")
} catch { print("error \(error)"); exit(4) }
