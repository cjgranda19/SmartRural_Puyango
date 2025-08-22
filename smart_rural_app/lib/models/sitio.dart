class Sitio {
  final String id;
  final String nombre;
  final String descripcion;
  final String imagen;
  final String accesibilidad;

  Sitio({
    required this.id,
    required this.nombre,
    required this.descripcion,
    required this.imagen,
    required this.accesibilidad,
  });

  factory Sitio.fromJson(Map<String, dynamic> json) {
    return Sitio(
      id: json['_id'],
      nombre: json['nombre'],
      descripcion: json['descripcion'],
      imagen: json['imagen'],
      accesibilidad: json['accesibilidad'] ?? 'desconocida',
    );
  }
}
