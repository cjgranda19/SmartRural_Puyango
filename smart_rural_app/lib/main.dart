import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'models/sitio.dart';
import 'resena_form.dart';
import 'ver_resenas_page.dart'; // Importa la vista de reseñas

Future<void> main() async {
  await dotenv.load(fileName: ".env");
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Smart Rural Puyango',
      theme: ThemeData(primarySwatch: Colors.green),
      home: const SitiosPage(),
    );
  }
}

Icon accesibilidadIcono(String nivel) {
  switch (nivel.toLowerCase()) {
    case 'alta':
      return const Icon(Icons.check_circle, color: Colors.green, size: 20);
    case 'media':
      return const Icon(Icons.error, color: Colors.orange, size: 20);
    case 'baja':
      return const Icon(Icons.cancel, color: Colors.red, size: 20);
    default:
      return const Icon(Icons.help_outline, color: Colors.grey, size: 20);
  }
}

class SitiosPage extends StatefulWidget {
  const SitiosPage({super.key});
  @override
  State<SitiosPage> createState() => _SitiosPageState();
}

class _SitiosPageState extends State<SitiosPage> {
  List<Sitio> sitios = [];
  bool cargando = true;

  @override
  void initState() {
    super.initState();
    cargarSitios();
  }

  Future<void> cargarSitios() async {
    final apiUrl = dotenv.env['API_URL'];
    final response = await http.get(Uri.parse('$apiUrl/sitios'));

    if (response.statusCode == 200) {
      final List<dynamic> data = json.decode(response.body);
      setState(() {
        sitios = data.map((s) => Sitio.fromJson(s)).toList();
        cargando = false;
      });
    } else {
      throw Exception('Error al cargar sitios');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Sitios Turísticos de Puyango')),
      body: cargando
          ? const Center(child: CircularProgressIndicator())
          : ListView.builder(
              itemCount: sitios.length,
              itemBuilder: (context, index) {
                final sitio = sitios[index];
                return Card(
                  margin: const EdgeInsets.all(12),
                  elevation: 4,
                  child: Padding(
                    padding: const EdgeInsets.all(12.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Image.network(
                          sitio.imagen,
                          width: double.infinity,
                          height: 180,
                          fit: BoxFit.cover,
                          errorBuilder: (context, error, stackTrace) =>
                              const Icon(Icons.broken_image, size: 100),
                        ),
                        const SizedBox(height: 10),
                        Text(
                          sitio.nombre,
                          style: const TextStyle(
                              fontSize: 18, fontWeight: FontWeight.bold),
                        ),
                        const SizedBox(height: 6),
                        Text(
                          sitio.descripcion,
                          style: const TextStyle(fontSize: 14),
                        ),
                        const SizedBox(height: 6),
                        Row(
                          children: [
                            accesibilidadIcono(sitio.accesibilidad),
                            const SizedBox(width: 6),
                            Text(
                              'Accesibilidad: ${sitio.accesibilidad}',
                              style: const TextStyle(
                                  fontSize: 14, fontWeight: FontWeight.w500),
                            ),
                          ],
                        ),
                        const SizedBox(height: 12),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                          children: [
                            ElevatedButton.icon(
                              onPressed: () {
                                Navigator.push(
                                  context,
                                  MaterialPageRoute(
                                    builder: (_) =>
                                        ResenaForm(sitioId: sitio.id),
                                  ),
                                );
                              },
                              icon: const Icon(Icons.rate_review),
                              label: const Text('Agregar Reseña'),
                            ),
                            ElevatedButton.icon(
                              onPressed: () {
                                Navigator.push(
                                  context,
                                  MaterialPageRoute(
                                    builder: (_) =>
                                        VerResenasPage(sitioId: sitio.id),
                                  ),
                                );
                              },
                              icon: const Icon(Icons.reviews),
                              label: const Text('Ver Reseñas'),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
    );
  }
}
