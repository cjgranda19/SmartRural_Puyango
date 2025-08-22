import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:flutter_dotenv/flutter_dotenv.dart';

class VerResenasPage extends StatefulWidget {
  final String sitioId;
  const VerResenasPage({super.key, required this.sitioId});

  @override
  State<VerResenasPage> createState() => _VerResenasPageState();
}

class _VerResenasPageState extends State<VerResenasPage> {
  List<dynamic> resenas = [];
  Map<String, dynamic>? resumen;
  bool cargando = true;

  @override
  void initState() {
    super.initState();
    cargarDatos();
  }

  String _baseUrl() {
    final env = dotenv.env['API_URL'];
    return (env != null && env.isNotEmpty) ? env : 'http://10.0.2.2:5000';
  }

  String _accText(dynamic v) {
    if (v is num) {
      if (v >= 0.7) return 'alta';
      if (v >= 0.4) return 'media';
      return 'baja';
    }
    if (v is String && v.isNotEmpty) return v.toLowerCase();
    return 'desconocida';
  }

  String _fechaToStr(dynamic v) {
    try {
      DateTime? d;
      if (v is String) d = DateTime.tryParse(v);
      if (v is Map && v[r'$date'] != null) {
        d = DateTime.tryParse(v[r'$date'].toString());
      }
      if (d != null) {
        final local = d.toLocal();
        return "${local.year.toString().padLeft(4,'0')}-${local.month.toString().padLeft(2,'0')}-${local.day.toString().padLeft(2,'0')}";
      }
    } catch (_) {}
    if (v is String && v.length >= 10) return v.substring(0, 10);
    return '';
  }

  Future<void> cargarDatos() async {
    final apiUrl = _baseUrl();
    final uriResenas = Uri.parse('$apiUrl/resenas/${widget.sitioId}');
    final uriResumen = Uri.parse('$apiUrl/resumen/${widget.sitioId}');

    try {
      final resenasResponse = await http
          .get(uriResenas, headers: {'Accept': 'application/json'})
          .timeout(const Duration(seconds: 12));
      final resumenResponse = await http
          .get(uriResumen, headers: {'Accept': 'application/json'})
          .timeout(const Duration(seconds: 12));

      if (resenasResponse.statusCode == 200 && resumenResponse.statusCode == 200) {
        final resenasJson = json.decode(utf8.decode(resenasResponse.bodyBytes));
        final resumenJson = json.decode(utf8.decode(resumenResponse.bodyBytes));

        final accTxt = _accText(resumenJson['accesibilidad']);
        resumenJson['accesibilidad_texto'] = resumenJson['accesibilidad_texto'] ?? accTxt;

        if (!mounted) return;
        setState(() {
          resenas = (resenasJson is List) ? resenasJson : [];
          resumen = (resumenJson is Map<String, dynamic>) ? resumenJson : {};
          cargando = false;
        });
      } else {
        if (!mounted) return;
        setState(() => cargando = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('HTTP ${resenasResponse.statusCode}/${resumenResponse.statusCode}: error al cargar')),
        );
      }
    } on TimeoutException {
      if (!mounted) return;
      setState(() => cargando = false);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Tiempo de espera agotado (timeout).')),
      );
    } catch (e) {
      if (!mounted) return;
      setState(() => cargando = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error de conexión: $e')),
      );
    }
  }

  Icon sentimientoIcono(dynamic sentimiento) {
    final s = (sentimiento ?? '').toString().toLowerCase();
    switch (s) {
      case 'positivo': return const Icon(Icons.sentiment_satisfied, color: Colors.green);
      case 'negativo': return const Icon(Icons.sentiment_dissatisfied, color: Colors.red);
      case 'neutral':  return const Icon(Icons.sentiment_neutral, color: Colors.grey);
      default:         return const Icon(Icons.help_outline);
    }
  }

  Icon accesibilidadIcono(String nivel) {
    switch (nivel.toLowerCase()) {
      case 'alta': return const Icon(Icons.traffic, color: Colors.green);
      case 'media': return const Icon(Icons.traffic, color: Colors.amber);
      case 'baja': return const Icon(Icons.traffic, color: Colors.red);
      default: return const Icon(Icons.help_outline);
    }
  }

  Widget _buildStatChip(String text, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: color, width: 1.5),
      ),
      child: Text(text, style: TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 12)),
    );
  }

  Color _getConclussionColor() {
    if (resumen == null) return Colors.grey;
    final c = (resumen!['conclusion'] ?? '').toString();
    if (c.contains('🟢')) return Colors.green;
    if (c.contains('🔴')) return Colors.red;
    if (c.contains('🔵')) return Colors.blue;
    return Colors.orange;
  }

  Color _getAccColor() {
    final t = (resumen?['accesibilidad_texto'] ?? '').toString().toLowerCase();
    switch (t) {
      case 'alta': return Colors.green;
      case 'media': return Colors.orange;
      case 'baja': return Colors.red;
      default: return Colors.grey;
    }
  }

  List<Widget> _buildRecommendationList(dynamic recomendacion) {
    List<String> items;
    if (recomendacion is List) {
      items = recomendacion.map((e) => e.toString()).toList();
    } else {
      items = recomendacion.toString().split(' | ');
    }
    return items.where((e) => e.trim().isNotEmpty).map((item) =>
      Padding(
        padding: const EdgeInsets.only(bottom: 8.0),
        child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Container(width: 6, height: 6, margin: const EdgeInsets.only(top: 6, right: 8),
              decoration: BoxDecoration(color: Colors.purple[400], shape: BoxShape.circle)),
          Expanded(child: Text(item, style: const TextStyle(fontSize: 14, height: 1.4))),
        ]),
      ),
    ).toList();
  }

  Widget _chipsExtraResumen() {
    final edad = (resumen?['edad_sugerida'] ?? 'sin datos').toString();
    final disc = (resumen?['discapacidad'] ?? 'sin datos').toString();
    final meses = (resumen?['mejores_meses'] is List)
        ? (resumen!['mejores_meses'] as List).join(', ')
        : 'sin datos';

    return Wrap(
      spacing: 8, runSpacing: 8, children: [
        _buildStatChip('🧒 $edad', Colors.blueGrey),
        _buildStatChip('♿ $disc', Colors.teal),
        _buildStatChip('📅 $meses', Colors.deepPurple),
      ],
    );
  }

  Widget _confianzaBadge() {
    final conf = resumen?['confianza'] as Map<String, dynamic>?;
    if (conf == null) return const SizedBox.shrink();
    final nivel = (conf['nivel'] ?? '').toString();
    final nTot = (conf['n_total'] ?? 0).toString();
    final n90  = (conf['n_ultimos_90d'] ?? 0).toString();
    Color c;
    switch (nivel) { case 'alta': c = Colors.green; break; case 'media': c = Colors.orange; break; default: c = Colors.red; }
    return _buildStatChip('📊 Confianza: ${nivel.toUpperCase()} (tot $nTot, 90d $n90)', c);
  }

  Widget _tagsWrap() {
    final tags = (resumen?['tags'] is List) ? List<String>.from(resumen!['tags']) : <String>[];
    if (tags.isEmpty) return const SizedBox.shrink();
    return Wrap(
      spacing: 8, runSpacing: 8,
      children: tags.map((t) => _buildStatChip('# $t', Colors.indigo)).toList(),
    );
  }

  Widget _trendBars() {
    final tend = (resumen?['tendencia'] is List) ? List<Map<String, dynamic>>.from(resumen!['tendencia']) : <Map<String,dynamic>>[];
    if (tend.isEmpty) return const SizedBox.shrink();
    final maxH = 60.0;
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(8), border: Border.all(color: Colors.grey[300]!)),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text("Tendencia (12 meses):", style: TextStyle(fontWeight: FontWeight.bold, color: Colors.blue[800])),
        const SizedBox(height: 8),
        SizedBox(height: maxH + 20,
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: tend.map((p) {
              final pct = (p['pct_positivo'] ?? 0).toDouble();
              final h = (pct/100.0)*maxH;
              return Expanded(
                child: Column(mainAxisAlignment: MainAxisAlignment.end, children: [
                  Container(height: h, margin: const EdgeInsets.symmetric(horizontal: 2),
                    decoration: BoxDecoration(color: Colors.blueAccent.withOpacity(0.6), borderRadius: BorderRadius.circular(4))),
                  const SizedBox(height: 4),
                  Text((p['mes'] ?? '').toString(), style: const TextStyle(fontSize: 10)),
                ]),
              );
            }).toList(),
          ),
        ),
      ]),
    );
  }

  Widget _mesesDetalle() {
    final det = (resumen?['detalle_meses'] is List) ? List<Map<String, dynamic>>.from(resumen!['detalle_meses']) : <Map<String,dynamic>>[];
    if (det.isEmpty) return const SizedBox.shrink();
    return ExpansionTile(
      title: const Text("Meses recomendados (detalle)"),
      children: det.map((m) =>
        ListTile(
          dense: true,
          leading: const Icon(Icons.event_available),
          title: Text("${m['mes']}"),
          trailing: Text("${m['positividad']}% • n=${m['n']}"),
        )
      ).toList(),
    );
  }

  Widget _alertasConsejos() {
    final alertas = (resumen?['alertas'] is List) ? List<String>.from(resumen!['alertas']) : <String>[];
    final consejos = (resumen?['consejos'] is List) ? List<String>.from(resumen!['consejos']) : <String>[];
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (alertas.isNotEmpty)
          Container(
            margin: const EdgeInsets.only(top: 8),
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(color: Colors.red[50], borderRadius: BorderRadius.circular(8), border: Border.all(color: Colors.red[200]!)),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text("Alertas:", style: TextStyle(fontWeight: FontWeight.bold, color: Colors.red[700])),
              const SizedBox(height: 6),
              ...alertas.map((a) => Padding(
                padding: const EdgeInsets.only(bottom: 6),
                child: Row(children: [
                  const Icon(Icons.warning_amber_rounded, size: 18, color: Colors.red),
                  const SizedBox(width: 6),
                  Expanded(child: Text(a)),
                ]),
              )),
            ]),
          ),
        if (consejos.isNotEmpty)
          Container(
            margin: const EdgeInsets.only(top: 8),
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(color: Colors.green[50], borderRadius: BorderRadius.circular(8), border: Border.all(color: Colors.green[200]!)),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text("Consejos:", style: TextStyle(fontWeight: FontWeight.bold, color: Colors.green[700])),
              const SizedBox(height: 6),
              ...consejos.map((c) => Padding(
                padding: const EdgeInsets.only(bottom: 6),
                child: Row(children: [
                  const Icon(Icons.check_circle, size: 18, color: Colors.green),
                  const SizedBox(width: 6),
                  Expanded(child: Text(c)),
                ]),
              )),
            ]),
          ),
      ],
    );
  }

  Widget _headerCard() {
    final accTxt = (resumen?['accesibilidad_texto'] ?? '').toString();
    final accVal = (resumen?['accesibilidad'] is num) ? (resumen!['accesibilidad'] as num).toDouble() : null;

    return Card(
      margin: const EdgeInsets.all(12), color: Colors.blue[50],
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            const Text("🖼️ ", style: TextStyle(fontSize: 22)),
            Text("Resumen Inteligente del Sitio",
              style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold, color: Colors.blue[800])),
          ]),
          const SizedBox(height: 12),

          // Stats rápidas
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(8), border: Border.all(color: Colors.grey[300]!)),
            child: Row(mainAxisAlignment: MainAxisAlignment.spaceAround, children: [
              _buildStatChip("✅ ${resumen!['porcentajes']['positivo']}%", Colors.green),
              _buildStatChip("😐 ${resumen!['porcentajes']['neutral']}%", Colors.orange),
              _buildStatChip("❌ ${resumen!['porcentajes']['negativo']}%", Colors.red),
            ]),
          ),

          const SizedBox(height: 12),
          Text("Total de reseñas: ${resumen!['total']}", style: const TextStyle(fontWeight: FontWeight.w500)),
          const SizedBox(height: 8),

          // Conclusión
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(color: _getConclussionColor(), borderRadius: BorderRadius.circular(8)),
            width: double.infinity,
            child: Text(resumen!['conclusion']?.toString() ?? '',
              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: Colors.white),
              textAlign: TextAlign.center),
          ),

          const SizedBox(height: 12),

          // Accesibilidad
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(color: Colors.grey[100], borderRadius: BorderRadius.circular(8)),
            child: Row(children: [
              const Text("🚗 Accesibilidad: ", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
              accesibilidadIcono(accTxt),
              const SizedBox(width: 8),
              Text(accTxt.toUpperCase(), style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: _getAccColor())),
              if (accVal != null) ...[
                const SizedBox(width: 8),
                Text("(${accVal.toStringAsFixed(2)})", style: const TextStyle(fontSize: 12, color: Colors.black54)),
              ]
            ]),
          ),

          const SizedBox(height: 8),
          _confianzaBadge(),
          const SizedBox(height: 8),
          _chipsExtraResumen(),
          const SizedBox(height: 8),
          _tagsWrap(),
          const SizedBox(height: 8),
          _trendBars(),
          _mesesDetalle(),

          // Recomendación detallada
          if (resumen!.containsKey('recomendacion') && resumen!['recomendacion'] != null) ...[
            const SizedBox(height: 16),
            Text("🤖 Recomendación Inteligente:", style: Theme.of(context).textTheme.titleMedium?.copyWith(
              fontWeight: FontWeight.bold, color: Colors.purple[700])),
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(color: Colors.purple[50], borderRadius: BorderRadius.circular(8), border: Border.all(color: Colors.purple[200]!)),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: _buildRecommendationList(resumen!['recomendacion'])),
            ),
          ],

          _alertasConsejos(),
        ]),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final header = (resumen == null)
        ? const SizedBox.shrink()
        : _headerCard();

    return Scaffold(
      appBar: AppBar(title: const Text('Reseñas del sitio')),
      body: cargando
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: cargarDatos,
              child: ListView.builder(
                itemCount: 1 + resenas.length,
                itemBuilder: (ctx, i) {
                  if (i == 0) return header;
                  final r = resenas[i - 1] as Map<String, dynamic>;
                  return Card(
                    margin: const EdgeInsets.symmetric(vertical: 10, horizontal: 12),
                    child: ListTile(
                      leading: sentimientoIcono(r['sentimiento']),
                      title: Text((r['texto'] ?? '').toString()),
                      subtitle: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                        Text('Usuario: ${r['usuario'] ?? 'Anónimo'}'),
                        Text('Fecha: ${_fechaToStr(r['fecha'])}', style: const TextStyle(fontSize: 12)),
                      ]),
                    ),
                  );
                },
              ),
            ),
    );
  }
}
