import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'dart:convert';

class ResenaForm extends StatefulWidget {
  final String sitioId;

  const ResenaForm({super.key, required this.sitioId});

  @override
  State<ResenaForm> createState() => _ResenaFormState();
}

class _ResenaFormState extends State<ResenaForm> {
  final _formKey = GlobalKey<FormState>();
  final _usuarioController = TextEditingController();
  final _textoController = TextEditingController();
  bool _enviando = false;

  Future<void> _enviarResena() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _enviando = true);

    final apiUrl = dotenv.env['API_URL'];
    final res = await http.post(
      Uri.parse('$apiUrl/resenas'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        "sitio_id": widget.sitioId,
        "usuario": _usuarioController.text,
        "texto": _textoController.text
      }),
    );

    setState(() => _enviando = false);

    if (res.statusCode == 201) {
      Navigator.pop(context, true);
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Error al enviar reseña')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Añadir Reseña')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Form(
          key: _formKey,
          child: Column(
            children: [
              TextFormField(
                controller: _usuarioController,
                decoration: const InputDecoration(labelText: 'Tu nombre'),
                validator: (value) => value!.isEmpty ? 'Campo obligatorio' : null,
              ),
              TextFormField(
                controller: _textoController,
                decoration: const InputDecoration(labelText: 'Tu opinión'),
                validator: (value) => value!.isEmpty ? 'Campo obligatorio' : null,
                maxLines: 4,
              ),
              const SizedBox(height: 20),
              ElevatedButton(
                onPressed: _enviando ? null : _enviarResena,
                child: _enviando
                    ? const CircularProgressIndicator()
                    : const Text('Enviar Reseña'),
              )
            ],
          ),
        ),
      ),
    );
  }
}
