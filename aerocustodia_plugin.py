import json
import urllib.request
import urllib.error
import urllib.parse
import tempfile
import os

def _validate_safe_url(target_url):
    """Verifica que la URL use unicamente esquemas http o https seguros."""
    parsed = urllib.parse.urlparse(target_url)
    if parsed.scheme not in ('http', 'https'):
        raise ValueError(f"Esquema de URL no permitido: {parsed.scheme}")
    return target_url
from qgis.PyQt.QtCore import Qt, QDate, QUrl
from qgis.PyQt.QtWidgets import (
    QAction, QMessageBox, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QDockWidget, QWidget, QComboBox, QDateEdit, QFileDialog, QDialog
)
from qgis.PyQt.QtGui import QIcon, QFont, QDesktopServices
class RadarDialog(QDialog):
    def __init__(self, parent, nivel, titulo, descripcion):
        super().__init__(parent)
        self.setWindowTitle("Clima")
        self.setFixedSize(550, 450)
        self.setStyleSheet("background-color: #1e1e24; color: #f5f5f5; font-family: 'Segoe UI', Arial;")
        
        layout = QVBoxLayout()
        layout.setContentsMargins(35, 30, 35, 25)
        
        lbl_icon = QLabel()
        if nivel == 4: icon_txt = "🌩️"
        elif nivel == 3: icon_txt = "🌧️"
        elif nivel == 2: icon_txt = "🌦️"
        else: icon_txt = "☀️"
        lbl_icon.setText(icon_txt)
        lbl_icon.setAlignment(Qt.AlignCenter)
        lbl_icon.setStyleSheet("font-size: 80px;")
        
        lbl_title = QLabel(titulo)
        lbl_title.setAlignment(Qt.AlignCenter)
        color = "#ff4444" if nivel == 4 else "#ff9800" if nivel == 3 else "#ffc107" if nivel == 2 else "#4caf50"
        lbl_title.setStyleSheet(f"font-size: 26px; font-weight: bold; color: {color}; margin-top: 5px;")
        
        lbl_desc = QLabel(descripcion)
        lbl_desc.setAlignment(Qt.AlignCenter)
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet("font-size: 15px; color: #cccccc; margin-top: 15px; margin-bottom: 20px;")
        
        lbl_disclaimer = QLabel("AeroCustodia es un Sistema de Soporte de Decisiones (DSS). Este diagnóstico se genera de forma automatizada procesando en tiempo real datos de la red global de OpenWeather cruzados matemáticamente con los límites geográficos (KML) de su establecimiento. La información tiene fines puramente preventivos y no constituye un parte oficial. Para alertas definitivas, por favor consulte siempre otras vías de comunicación y del Servicio Meteorológico Nacional (SMN).")
        lbl_disclaimer.setWordWrap(True)
        lbl_disclaimer.setAlignment(Qt.AlignJustify)
        lbl_disclaimer.setStyleSheet("font-size: 11px; color: #888888; margin-top: 20px; border-top: 1px solid #333333; padding-top: 15px;")
        
        layout.addWidget(lbl_icon)
        layout.addWidget(lbl_title)
        layout.addWidget(lbl_desc)
        layout.addStretch()
        layout.addWidget(lbl_disclaimer)
        
        self.setLayout(layout)

class AeroCustodiaPlugin:

    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.action = None
        self.dockwidget = None

    def initGui(self):
        icon_path = os.path.join(self.plugin_dir, 'icon.png')
        self.action = QAction(QIcon(icon_path), 'AeroCustodia - Analizador de Lotes', self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu('&AeroCustodia', self.action)


    def _abrir_registro(self):
        safe_url = _validate_safe_url("https://www.aerocustodia.com.ar/registro/")
        QDesktopServices.openUrl(QUrl(safe_url))

    def unload(self):
        self.iface.removeToolBarIcon(self.action)
        self.iface.removePluginMenu('&AeroCustodia', self.action)
        if self.dockwidget:
            self.iface.removeDockWidget(self.dockwidget)

    def run(self):
        if not self.dockwidget:
            self.dockwidget = QDockWidget("AeroCustodia", self.iface.mainWindow())
            widget = QWidget()
            
            lbl_api = QLabel("AeroCustodia API Key:")
            self.txt_api = QLineEdit()
            self.txt_api.setPlaceholderText("Ej: ac_live_123456789")
            self.txt_api.setEchoMode(QLineEdit.Password)
            
            self.btn_get_key = QPushButton("🎁 ¿No tenés API Key? Obtené 10 créditos gratis")
            self.btn_get_key.setStyleSheet(
                "background-color: transparent; color: #00ff88; border: 1px dashed #00ff88; "
                "font-size: 11px; font-weight: bold; padding: 5px; border-radius: 4px; text-align: center;"
            )
            self.btn_get_key.setToolTip("Abre aerocustodia.com.ar para registrarte gratis y recibir 10 créditos de bienvenida.")
            self.btn_get_key.clicked.connect(self._abrir_registro)
            
            lbl_tipo = QLabel("Tipo de Auditoría:")
            self.cmb_tipo = QComboBox()
            self.cmb_tipo.addItem("🌧️ Riesgo Hídrico (JRC Global Surface Water)", "water")
            self.cmb_tipo.addItem("🌲 Certificación EUDR (Deforestación Cero)", "eudr")
            self.cmb_tipo.addItem("⛰️ Relieve y Topografía (DEM SRTM 30m)", "dem")
            self.cmb_tipo.addItem("🌱 Salud Vegetal / Biomasa (Índice NDVI)", "ndvi")
            self.cmb_tipo.addItem("⛈️ Precipitaciones Acumuladas 15 días (GPM)", "gpm")
            self.cmb_tipo.addItem("💧 Humedad de Suelo Superficial (SMAP)", "smap")
            self.cmb_tipo.addItem("⛅ Clima (12h)", "clima")
            
            # --- SELECTOR DE PERÍODO TEMPORAL (NDVI) ---
            self.lbl_periodo = QLabel("📅 Ventana Temporal (NDVI):")
            self.cmb_periodo = QComboBox()
            self.cmb_periodo.addItem("🟢 Estado Actual (Últimos 15 días - Recorrida)", "15d")
            self.cmb_periodo.addItem("🟡 Último Mes (Últimos 30 días)", "30d")
            self.cmb_periodo.addItem("🔵 Trimestre Reciente (Últimos 60 días)", "60d")
            self.cmb_periodo.addItem("🗓️ Personalizado (Elegir Fechas)", "custom")
            
            self.custom_dates_widget = QWidget()
            layout_dates = QHBoxLayout()
            layout_dates.setContentsMargins(0, 0, 0, 0)
            self.date_start = QDateEdit()
            self.date_start.setCalendarPopup(True)
            self.date_start.setDate(QDate.currentDate().addDays(-15))
            self.date_end = QDateEdit()
            self.date_end.setCalendarPopup(True)
            self.date_end.setDate(QDate.currentDate())
            layout_dates.addWidget(QLabel("Desde:"))
            layout_dates.addWidget(self.date_start)
            layout_dates.addWidget(QLabel("Hasta:"))
            layout_dates.addWidget(self.date_end)
            self.custom_dates_widget.setLayout(layout_dates)
            self.custom_dates_widget.setVisible(False)
            
            self.cmb_periodo.currentIndexChanged.connect(self._toggle_custom_dates)
            self.cmb_tipo.currentIndexChanged.connect(self._toggle_ndvi_period)
            
            # Inicialmente ocultos hasta que se seleccione NDVI
            self.lbl_periodo.setVisible(False)
            self.cmb_periodo.setVisible(False)
            
            self.btn_analizar = QPushButton("🛰️ Analizar Lote Seleccionado")
            self.btn_analizar.setStyleSheet("background-color: #28a745; color: white; font-weight: bold; padding: 9px; border-radius: 4px;")
            self.btn_analizar.clicked.connect(self.procesar_lote)
            
            self.btn_geopdf = QPushButton("📲 Exportar GeoPDF (Avenza / FO Maps)")
            self.btn_geopdf.setStyleSheet("background-color: #0284c7; color: white; font-weight: bold; padding: 9px; border-radius: 4px;")
            self.btn_geopdf.setToolTip("Exporta el mapa actual con GPS georreferenciado para abrirlo y recorrer el lote con el teléfono celular.")
            self.btn_geopdf.clicked.connect(self.exportar_geopdf)
            
            self.lbl_status = QLabel("Listo. Seleccione una capa vectorial.")
            self.lbl_status.setWordWrap(True)
            
            layout = QVBoxLayout()
            layout.addWidget(lbl_api)
            layout.addWidget(self.txt_api)
            layout.addWidget(self.btn_get_key)
            layout.addSpacing(10)
            layout.addWidget(lbl_tipo)
            layout.addWidget(self.cmb_tipo)
            layout.addSpacing(6)
            layout.addWidget(self.lbl_periodo)
            layout.addWidget(self.cmb_periodo)
            layout.addWidget(self.custom_dates_widget)
            layout.addSpacing(12)
            layout.addWidget(self.btn_analizar)
            layout.addSpacing(8)
            layout.addWidget(self.btn_geopdf)
            layout.addSpacing(10)
            layout.addWidget(self.lbl_status)
            layout.addStretch()
            widget.setLayout(layout)
            
            self.dockwidget.setWidget(widget)
            self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dockwidget)
        
        self.dockwidget.show()

    def procesar_lote(self):
        try:
            tipo_audit_early = self.cmb_tipo.currentData()
            api_key = self.txt_api.text()
            if not api_key and tipo_audit_early != "clima":
                reply = QMessageBox.question(
                    self.iface.mainWindow(),
                    "AeroCustodia - Se requiere API Key",
                    "Para realizar análisis satelitales en la nube se requiere una API Key.\n\n"
                    "¿Desea abrir aerocustodia.com.ar para registrarse y obtener 10 créditos gratuitos de bienvenida?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                if reply == QMessageBox.Yes:
                    self._abrir_registro()
                return
            
            layer = self.iface.activeLayer()
            from qgis.core import QgsMapLayerType
            if not layer or layer.type() != QgsMapLayerType.VectorLayer:
                QMessageBox.warning(self.iface.mainWindow(), "AeroCustodia - Error", "⚠️ Seleccione una capa vectorial (polígono) en el panel de capas.")
                return
            
            features = list(layer.getFeatures())
            if not features:
                QMessageBox.warning(self.iface.mainWindow(), "AeroCustodia - Error", "⚠️ La capa seleccionada esta vacia.")
                return
            
            from qgis.core import QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject
        
            crs_src = layer.crs()
            crs_dest = QgsCoordinateReferenceSystem("EPSG:4326")
            transform = QgsCoordinateTransform(crs_src, crs_dest, QgsProject.instance())
        
            geom = features[0].geometry()
            geom.transform(transform)
            geom_json_str = geom.asJson()
            geom_dict = json.loads(geom_json_str)
            
            tipo_audit = self.cmb_tipo.currentData()
            if tipo_audit == "clima":
                self.ejecutar_radar_clima(features)
                return

            
            # --- VALIDACION LOCAL DE AREA (5000 Ha) ---
            from qgis.core import QgsDistanceArea
            import math
            da = QgsDistanceArea()
            da.setEllipsoid('WGS84')
            da.setSourceCrs(crs_src, QgsProject.instance().transformContext())
            
            area_sqm = da.measureArea(features[0].geometry())
            area_ha = area_sqm / 10000.0
            required_credits = max(1, math.ceil(area_ha / 5000.0))
            
            if area_ha > 5000.0:
                reply = QMessageBox.question(self.iface.mainWindow(), 'AeroCustodia - Límite Excedido', 
                                             f'El lote seleccionado mide {area_ha:,.2f} hectáreas.\n\nAl superar la franquicia de 5.000 Ha, este procesamiento consumirá {required_credits} créditos en lugar de 1.\n\n¿Desea continuar?',
                                             QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.No:
                    return
            # ------------------------------------------
        
            self.lbl_status.setText("⌛ Calculando Auditoría en la Nube (Google Earth Engine)...")
            self.lbl_status.setStyleSheet("color: #004085; font-weight: bold;")
        
            analysis_type = self.cmb_tipo.currentData()
        
            url = "https://www.aerocustodia.com.ar/auditoria/api/qgis/analyze/"
        
            payload = {
                "api_key": api_key,
                "geometry": geom_dict,
                "analysis_type": analysis_type
            }
            if analysis_type == 'ndvi':
                time_win = self.cmb_periodo.currentData()
                payload["time_window"] = time_win
                if time_win == "custom":
                    payload["start_date"] = self.date_start.date().toString("yyyy-MM-dd")
                    payload["end_date"] = self.date_end.date().toString("yyyy-MM-dd")
        
            try:
                _validate_safe_url(url)
                headers = {
                    'Content-Type': 'application/json',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AeroCustodia-QGIS/1.0'
                }
                req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers)
                response = urllib.request.urlopen(req, timeout=30)  # nosec B310
                result = json.loads(response.read().decode('utf-8'))
            
                download_url = result.get('download_url')
                self.current_start_date = result.get('start_date')
                self.current_end_date = result.get('end_date')
                if not download_url:
                    raise Exception("El servidor no devolvió una URL de descarga.")
                
                self.lbl_status.setText("📥 Descargando archivo GeoTIFF crudo...")
            
                temp_dir = tempfile.gettempdir()
                tif_filename = f"aerocustodia_{analysis_type}.tif"
                tif_path = os.path.join(temp_dir, tif_filename)
                _validate_safe_url(download_url)
                urllib.request.urlretrieve(download_url, tif_path)  # nosec B310
            
                layer_name = f"AeroCustodia - {self.cmb_tipo.currentText()}"
                raster_layer = self.iface.addRasterLayer(tif_path, layer_name)
            
                if raster_layer and raster_layer.isValid():
                    self.lbl_status.setText("🎨 Aplicando estética satelital y bordes...")

                    # --- CARTOGRAFIA DINAMICA ---
                    from qgis.core import QgsColorRampShader, QgsRasterShader, QgsSingleBandPseudoColorRenderer, QgsRasterBandStats
                    from PyQt5.QtGui import QColor

                    # Forzamos calculo de estadisticas para obtener Min/Max reales de este raster
                    provider = raster_layer.dataProvider()
                    stats = provider.bandStatistics(1, QgsRasterBandStats.All)
                    rmin = stats.minimumValue
                    rmax = stats.maximumValue

                    fnc = QgsColorRampShader()
                    fnc.setColorRampType(QgsColorRampShader.Interpolated)
                    
                    if analysis_type == 'smap':
                        # Humedad (Gris/Amarillo seco -> Azul humedo)
                        fnc.setColorRampItemList([
                            QgsColorRampShader.ColorRampItem(rmin, QColor('#ffffd4'), f'{round(rmin,2)} (Seco)'),
                            QgsColorRampShader.ColorRampItem(rmin + (rmax-rmin)*0.5, QColor('#41b6c4'), 'Medio'),
                            QgsColorRampShader.ColorRampItem(rmax, QColor('#253494'), f'{round(rmax,2)} (Húmedo)')
                        ])
                    elif analysis_type == 'ndvi':
                        # NDVI (Rojo -> Amarillo -> Verde Oscuro)
                        fnc.setColorRampItemList([
                            QgsColorRampShader.ColorRampItem(rmin, QColor('#d73027'), 'Bajo Vigor'),
                            QgsColorRampShader.ColorRampItem(rmin + (rmax-rmin)*0.5, QColor('#ffffbf'), 'Medio'),
                            QgsColorRampShader.ColorRampItem(rmax, QColor('#1a9850'), 'Alto Vigor')
                        ])
                    elif analysis_type == 'gpm':
                        # Lluvia (Blanco -> Celeste -> Azul oscuro)
                        fnc.setColorRampItemList([
                            QgsColorRampShader.ColorRampItem(rmin, QColor('#f7fbff'), f'{round(rmin,1)} mm'),
                            QgsColorRampShader.ColorRampItem(rmin + (rmax-rmin)*0.5, QColor('#6baed6'), 'Medio'),
                            QgsColorRampShader.ColorRampItem(rmax, QColor('#08306b'), f'{round(rmax,1)} mm')
                        ])
                    elif analysis_type == 'dem':
                        # Topografia (Verde -> Amarillo -> Marron)
                        fnc.setColorRampItemList([
                            QgsColorRampShader.ColorRampItem(rmin, QColor('#33a02c'), f'{round(rmin,1)} m'),
                            QgsColorRampShader.ColorRampItem(rmin + (rmax-rmin)*0.5, QColor('#e31a1c'), 'Medio'),
                            QgsColorRampShader.ColorRampItem(rmax, QColor('#b15928'), f'{round(rmax,1)} m')
                        ])
                    elif analysis_type == 'eudr':
                        # Deforestacion (Transparente o Rojo)
                        fnc.setColorRampType(QgsColorRampShader.Exact)
                        fnc.setColorRampItemList([
                            QgsColorRampShader.ColorRampItem(0, QColor(0,0,0,0), 'Bosque Intacto'),
                            QgsColorRampShader.ColorRampItem(1, QColor('#e31a1c'), 'Deforestación post-2020')
                        ])
                    else:
                        # Por defecto (Riesgo Hidrico)
                        fnc.setColorRampItemList([
                            QgsColorRampShader.ColorRampItem(0, QColor(255, 255, 255, 0), '0% (Seco)'),
                            QgsColorRampShader.ColorRampItem(rmax*0.1, QColor(224, 243, 255, 200), 'Ocasional'),
                            QgsColorRampShader.ColorRampItem(rmax*0.5, QColor(51, 153, 255, 255), 'Frecuente'),
                            QgsColorRampShader.ColorRampItem(rmax, QColor(0, 0, 153, 255), 'Permanente')
                        ])

                    shader = QgsRasterShader()
                    shader.setRasterShaderFunction(fnc)
                    renderer = QgsSingleBandPseudoColorRenderer(provider, 1, shader)
                    raster_layer.setRenderer(renderer)
                    raster_layer.triggerRepaint()
                    self.iface.layerTreeView().refreshLayerSymbology(raster_layer.id())
                    from qgis.core import QgsRasterLayer, QgsProject, QgsFillSymbol, QgsSingleSymbolRenderer
                
                    url_google = "type=xyz&url=https://mt1.google.com/vt/lyrs=s%26x={x}%26y={y}%26z={z}&zmax=19&zmin=0"
                    google_layer = QgsRasterLayer(url_google, "Google Satellite", "wms")
                    if google_layer.isValid():
                        QgsProject.instance().addMapLayer(google_layer, False)
                        root = QgsProject.instance().layerTreeRoot()
                        root.insertLayer(-1, google_layer) 
                
                    symbol = QgsFillSymbol.createSimple({'color': '0,0,0,0', 'outline_color': '#39FF14', 'outline_width': '0.8'})
                    vector_renderer = QgsSingleSymbolRenderer(symbol)
                    layer.setRenderer(vector_renderer)
                    layer.triggerRepaint()
                    self.iface.layerTreeView().refreshLayerSymbology(layer.id())
                
                    self.lbl_status.setText("📄 Armando el Reporte Profesional (PDF)...")
                    self.generar_layout(raster_layer, layer, analysis_type)
            
                self.lbl_status.setText("✅ ¡Auditoría Lista!")
                self.lbl_status.setStyleSheet("color: #28a745; font-weight: bold;")
            
                QMessageBox.information(
                    self.iface.mainWindow(), 
                    "AeroCustodia", 
                    "✅ ¡Análisis Completado!\n\nEl mapa fue descargado y el Reporte Profesional ya está armado en tu Administrador de Composiciones."
                )
            
            except urllib.error.HTTPError as e:
                error_data = {}
                try:
                    error_data = json.loads(e.read().decode('utf-8'))
                except Exception as parse_err:
                    error_data = {'message': f'HTTP Error {e.code}: {str(parse_err)}'}
            
                msg = error_data.get('message', 'Error desconocido del servidor.')
            
                if e.code == 402:
                    msg = f"❌ Créditos insuficientes:\n{msg}"
                elif e.code == 403:
                    msg = f"❌ Error de Autorización:\n{msg}"
                
                QMessageBox.critical(self.iface.mainWindow(), "AeroCustodia - Error", msg)
                self.lbl_status.setText("❌ Error de comunicación con la API.")
                self.lbl_status.setStyleSheet("color: #dc3545; font-weight: bold;")
            except Exception as e:
                QMessageBox.critical(self.iface.mainWindow(), "AeroCustodia - Error", f"❌ Error descargando el mapa.\nDetalle: {str(e)}")
                self.lbl_status.setText("❌ Error en la descarga.")
                self.lbl_status.setStyleSheet("color: #dc3545; font-weight: bold;")

        except Exception as e:
            import traceback
            QMessageBox.critical(self.iface.mainWindow(), "Error Crítico Oculto", str(traceback.format_exc()))



    def ejecutar_radar_clima(self, features):
        import urllib.request
        import urllib.error
        import json
        from qgis.PyQt.QtWidgets import QMessageBox
        try:
            geom = features[0].geometry()
            centroid = geom.pointOnSurface().asPoint()
            lat = centroid.y()
            lon = centroid.x()
            
            self.lbl_status.setText("🌤 Consultando Clima en el servidor...")
            
            url = "https://www.aerocustodia.com.ar/auditoria/api/qgis/clima/"
            _validate_safe_url(url)
            data = json.dumps({'lat': lat, 'lon': lon}).encode('utf-8')
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AeroCustodia-QGIS/1.0'
            }
            req = urllib.request.Request(url, data=data, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as response:  # nosec B310
                if response.status == 200:
                    resp_data = json.loads(response.read().decode())
                    
                    peor_nivel = resp_data.get('nivel', 1)
                    titulo = resp_data.get('titulo', 'Clima')
                    desc = resp_data.get('descripcion', '')
                    
                    self.lbl_status.setText("✅ Consulta de clima completada.")
                    
                    dialog = RadarDialog(self.iface.mainWindow(), peor_nivel, titulo, desc)
                    dialog.exec_()
                else:
                    self.lbl_status.setText("❌ Error del servidor.")
                    QMessageBox.warning(self.iface.mainWindow(), "Error", f"Error {response.status}")
                    
        except urllib.error.URLError as e:
            self.lbl_status.setText("❌ Error de conexión.")
            if isinstance(e.reason, TimeoutError) or "timeout" in str(e.reason).lower():
                QMessageBox.warning(self.iface.mainWindow(), "Timeout", "El servidor tardó demasiado en responder.")
            else:
                QMessageBox.warning(self.iface.mainWindow(), "Error de red", str(e.reason))
        except Exception as e:
            self.lbl_status.setText("❌ Error consultando clima.")
            QMessageBox.warning(self.iface.mainWindow(), "Error", str(e))
    def generar_layout(self, raster_layer, vector_layer, analysis_type):
        from qgis.core import QgsProject, QgsPrintLayout, QgsLayoutItemMap, QgsLayoutItemLabel, QgsLayoutItemLegend, QgsLayoutPoint, QgsLayoutSize
        from PyQt5.QtGui import QFont
        
        project = QgsProject.instance()
        manager = project.layoutManager()
        
        layout_name = "Reporte AeroCustodia"
        existing = manager.layoutByName(layout_name)
        if existing:
            manager.removeLayout(existing)
            
        layout = QgsPrintLayout(project)
        layout.initializeDefaults() 
        layout.setName(layout_name)
        manager.addLayout(layout)
        
        from qgis.core import QgsLayoutItemPage
        page1 = layout.pageCollection().pages()[0]
        page1.setPageSize("A4", QgsLayoutItemPage.Portrait)
        
        title = QgsLayoutItemLabel(layout)
        title.setText("Auditoría Territorial Integral")
        title.setFont(QFont("Arial", 20, QFont.Bold))
        title.adjustSizeToText()
        layout.addLayoutItem(title)
        title.attemptMove(QgsLayoutPoint(10, 10))
        
        map_item = QgsLayoutItemMap(layout)
        map_item.setRect(20, 20, 20, 20)
        
        extent = vector_layer.extent()
        extent.scale(1.2)
        
        map_item.setExtent(extent)
        layout.addLayoutItem(map_item)
        
        map_item.attemptMove(QgsLayoutPoint(10, 30))
        map_item.attemptResize(QgsLayoutSize(190, 250))
        
        grid = map_item.grid()
        grid.setEnabled(True)
        grid.setIntervalX(0.01)
        grid.setIntervalY(0.01)
        grid.setAnnotationEnabled(True)
        grid.setAnnotationFont(QFont("Arial", 8))
        
        page2 = QgsLayoutItemPage(layout)
        page2.setPageSize("A4", QgsLayoutItemPage.Portrait)
        layout.pageCollection().addPage(page2)
        
        title2 = QgsLayoutItemLabel(layout)
        title2.setText("Anexo Técnico y Metodológico")
        title2.setFont(QFont("Arial", 16, QFont.Bold))
        title2.adjustSizeToText()
        layout.addLayoutItem(title2)
        title2.attemptMove(QgsLayoutPoint(10, 10), page=1) 
        
        legend = QgsLayoutItemLegend(layout)
        legend.setTitle("Referencias")
        layout.addLayoutItem(legend)
        legend.attemptMove(QgsLayoutPoint(10, 30), page=1)
        
        disclaimer = QgsLayoutItemLabel(layout)
        
        if analysis_type == 'eudr':
            disclaimer_text = (
                "CERTIFICACIÓN DE DEFORESTACIÓN CERO (Reglamento UE 2023/1115)\n\n"
                "Metodología: Este análisis utiliza el catálogo satelital Hansen Global Forest Change "
                "(Universidad de Maryland) para auditar cambios en la cobertura forestal.\n\n"
                "Resultado: Se analizó el polígono declarado para verificar la existencia de píxeles "
                "que indiquen pérdida de bosque con posterioridad al 31 de Diciembre de 2020. "
                "Las áreas marcadas en ROJO en el mapa representan deforestación detectada post-2020. "
                "Si no existen píxeles rojos, el lote CUMPLE con la normativa EUDR.\n\n"
                "DISCLAIMER LEGAL: Este certificado es generado de forma automatizada mediante "
                "Inteligencia Artificial y datos satelitales públicos. No reemplaza a las auditorías "
                "oficiales ni exime al exportador de sus obligaciones legales de diligencia debida."
            )
        elif analysis_type == 'dem':
            disclaimer_text = (
                "AUDITORÍA TOPOGRÁFICA Y DE RELIEVE (Modelo Digital de Elevación)\n\n"
                "Metodología: Se procesó el Modelo Digital de Elevación SRTM (Shuttle Radar Topography Mission) "
                "de la NASA, provisto a través de Google Earth Engine, con una resolución espacial de 30 metros.\n\n"
                "Análisis Hidrológico Primario: El mapa exhibe la variación altimétrica del lote en metros sobre "
                "el nivel del mar (msnm). Las curvas de nivel trazadas permiten inferir las pendientes naturales "
                "del terreno y predecir el escurrimiento de las aguas pluviales.\n\n"
                "Utilidad Agronómica: Este insumo es vital para el diseño de curvas de nivel, terrazas, "
                "canales de drenaje y para prevenir zonas de erosión y anegamiento hídrico.\n\n"
                "DISCLAIMER LEGAL: Las altitudes son promedios satelitales (MDT) y no reemplazan una nivelación "
                "topográfica de precisión realizada en el terreno."
            )
        elif analysis_type == 'ndvi':
            disclaimer_text = (
                "AUDITORÍA DE SALUD VEGETAL (ÍNDICE NDVI)\n\n"
                "Metodología: Este análisis captura el Índice de Diferencia Normalizada de Vegetación (NDVI) "
                "utilizando la constelación satelital Sentinel-2 (Agencia Espacial Europea) con resolución de 10 metros.\n\n"
                "Filtro Temporal Dinámico: Para asegurar la máxima precisión actual, el sistema busca automáticamente "
                "la imagen más reciente de los últimos 60 días que posea el menor porcentaje de cobertura nubosa "
                "sobre el polígono declarado.\n\n"
                "Interpretación: Valores cercanos a 1 (Verde Oscuro) indican alta biomasa y fotosíntesis activa. "
                "Valores cercanos a 0 (Rojo/Naranja) indican suelo desnudo, estrés hídrico severo o áreas anegadas.\n\n"
                "DISCLAIMER: El NDVI es una medición radiométrica relativa al momento de la captura satelital y debe "
                "ser validada a campo por un profesional agrónomo."
            )
        elif analysis_type == 'gpm':
            disclaimer_text = (
                "AUDITORÍA DE PRECIPITACIONES (GPM/CHIRPS)\n\n"
                "Metodología: El análisis calcula la cantidad total de milímetros de lluvia caídos sobre el polígono "
                "durante los últimos 15 días, sumando las capturas diarias de radares satelitales.\n\n"
                "Problema Resuelto: Supera la limitación de la interpolación de estaciones meteorológicas dispersas, "
                "midiendo la lluvia real y localizada desde el espacio.\n\n"
                "DISCLAIMER: Los datos satelitales de precipitaciones pueden tener un margen de error radiométrico y "
                "no reemplazan a un pluviómetro físico instalado in situ en el establecimiento."
            )
        elif analysis_type == 'smap':
            disclaimer_text = (
                "AUDITORÍA DE HUMEDAD DE SUELO (SMAP)\n\n"
                "Metodología: El análisis extrae la humedad volumétrica superficial de los últimos 7 días "
                "mediante la misión SMAP (Soil Moisture Active Passive) de la NASA, que utiliza radares de microondas.\n\n"
                "Ventaja Agronómica: A diferencia de la lluvia acumulada, este índice refleja cuánta de esa agua "
                "realmente penetró y se mantuvo en los primeros centímetros del suelo.\n\n"
                "DISCLAIMER: La humedad de suelo satelital se mide a gran escala y se ve afectada por la cobertura vegetal "
                "y el tipo de suelo. Requiere calibración a campo."
            )
        else:
            disclaimer_text = (
                "Este reporte constituye una Auditoría Territorial Satelital que integra múltiples fuentes de "
                "datos geoespaciales para el análisis del lote:\n\n"
                "1. Riesgo Hídrico (Memoria del Lote): Calculado en base al catálogo JRC Global Surface Water. "
                "Representa un promedio histórico procesando imágenes satelitales desde 1984 hasta 2021 (38 años).\n\n"
                "2. Topografía y Relieve: Modelo de Elevación Digital (DEM) derivado de misiones satelitales (SRTM / Copernicus).\n\n"
                "3. Vigor Vegetal (NDVI): Índice procesado mediante Sentinel-2 (ESA).\n\n"
                "DISCLAIMER LEGAL: Este documento es un diagnóstico satelital preliminar automatizado."
            )

        if hasattr(self, 'current_start_date') and self.current_start_date:
            if self.current_start_date == getattr(self, 'current_end_date', None):
                fecha_texto = f"\n\n🕒 Fecha de la imagen satelital analizada: {self.current_start_date}"
            else:
                fecha_texto = f"\n\n🕒 Período analizado por el radar: {self.current_start_date} al {getattr(self, 'current_end_date', '')}"
            disclaimer_text += fecha_texto

        disclaimer.setText(disclaimer_text)
        disclaimer.setFont(QFont("Arial", 10))
        layout.addLayoutItem(disclaimer)
        
        disclaimer.attemptMove(QgsLayoutPoint(10, 110), page=1)
        disclaimer.attemptResize(QgsLayoutSize(190, 150))
        
        self.iface.openLayoutDesigner(layout)

    def _toggle_custom_dates(self):
        is_custom = self.cmb_periodo.currentData() == "custom"
        self.custom_dates_widget.setVisible(is_custom)

    def _toggle_ndvi_period(self):
        is_ndvi = self.cmb_tipo.currentData() == "ndvi"
        self.lbl_periodo.setVisible(is_ndvi)
        self.cmb_periodo.setVisible(is_ndvi)
        if not is_ndvi:
            self.custom_dates_widget.setVisible(False)
        else:
            self.custom_dates_widget.setVisible(self.cmb_periodo.currentData() == "custom")

    def exportar_geopdf(self):
        try:
            layer = self.iface.activeLayer()
            if not layer:
                QMessageBox.warning(self.iface.mainWindow(), "AeroCustodia", "⚠️ Por favor, seleccione la capa del lote o del mapa satelital en el panel de capas.")
                return

            file_path, _ = QFileDialog.getSaveFileName(
                self.iface.mainWindow(),
                "Guardar GeoPDF para Avenza Maps / FO Maps",
                os.path.join(os.path.expanduser("~"), "Lote_AeroCustodia_Avenza.pdf"),
                "Documento PDF Geoespacial (*.pdf)"
            )
            if not file_path:
                return

            self.lbl_status.setText("📲 Generando PDF Geoespacial para celular...")
            self.lbl_status.setStyleSheet("color: #0284c7; font-weight: bold;")

            from qgis.core import (
                QgsProject, QgsPrintLayout, QgsLayoutItemMap, 
                QgsLayoutExporter, QgsLayoutSize, QgsLayoutPoint, QgsUnitTypes
            )

            project = QgsProject.instance()
            layout_name = "AeroCustodia_GeoPDF_Mobile"
            
            # Limpiar layout previo con el mismo nombre si existiera
            layout_manager = project.layoutManager()
            existing = layout_manager.layoutByName(layout_name)
            if existing:
                layout_manager.removeLayout(existing)

            layout = QgsPrintLayout(project)
            layout.initializeDefaults()
            layout.setName(layout_name)

            # Pagina A4 Horizontal
            page = layout.pageCollection().page(0)
            page.setPageSize("A4", QgsLayoutItemMap.Orientation.Landscape)

            # Mapa ocupando la pagina completa (297 x 210 mm)
            map_item = QgsLayoutItemMap(layout)
            map_item.setRect(0, 0, 297, 210)
            map_item.attemptMove(QgsLayoutPoint(0, 0, QgsUnitTypes.LayoutMillimeters))
            map_item.attemptResize(QgsLayoutSize(297, 210, QgsUnitTypes.LayoutMillimeters))

            # Ajustar encuadre al lote con 10% de margen
            extent = layer.extent()
            extent.scale(1.1)
            map_item.setExtent(extent)
            layout.addLayoutItem(map_item)

            # Exportar con georreferenciacion GeoPDF activa
            settings = QgsLayoutExporter.PdfExportSettings()
            settings.dpi = 300
            settings.rasterizeWholeImage = False
            settings.appendGeoreference = True
            try:
                settings.exportFlags = QgsLayoutExporter.FlagIncludeGeoPdfFeatures
            except (AttributeError, Exception) as flag_err:
                settings.appendGeoreference = True

            exporter = QgsLayoutExporter(layout)
            res = exporter.exportToPdf(file_path, settings)

            if res == QgsLayoutExporter.Success:
                self.lbl_status.setText("✅ ¡GeoPDF exportado con éxito!")
                self.lbl_status.setStyleSheet("color: #28a745; font-weight: bold;")
                QMessageBox.information(
                    self.iface.mainWindow(),
                    "AeroCustodia - GeoPDF Listo",
                    f"✅ ¡Archivo GeoPDF generado con éxito!\n\n"
                    f"Ubicación:\n{file_path}\n\n"
                    "📲 Pasos para usarlo a campo:\n"
                    "1. Envía este archivo PDF a tu teléfono (por WhatsApp, Drive o cable).\n"
                    "2. Ábrelo con la app Avenza Maps o FO Maps.\n"
                    "3. ¡Listo! Podrás recorrer el lote y ver tu posición GPS en tiempo real arriba del mapa satelital sin necesidad de señal de internet."
                )
            else:
                QMessageBox.warning(self.iface.mainWindow(), "AeroCustodia", f"No se pudo exportar el GeoPDF (Código error: {res}).")

        except Exception as e:
            QMessageBox.critical(self.iface.mainWindow(), "AeroCustodia - Error", f"Error al generar GeoPDF: {str(e)}")
