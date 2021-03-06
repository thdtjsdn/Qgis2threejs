# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Qgis2threejs
                                 A QGIS plugin
 export terrain and map image into web browser
                              -------------------
        begin                : 2013-12-21
        copyright            : (C) 2013 by Minoru Akagi
        email                : akaginch@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from qgis.core import *

class QuadNode:
  def __init__(self, parent, extent, location, depth=0):
    self.parent = parent
    self.extent = extent
    self.location = location
    self.depth = depth
    self.subNodes = []

  def subdivideRecursively(self, point, maxDepth):
    if maxDepth <= self.depth:
      return
    self.subNodes = []
    for y in range(2):
      for x in range(2):
        xmin = self.extent.xMinimum() + 0.5 * x * self.extent.width()
        ymin = self.extent.yMinimum() + 0.5 * (1 - y) * self.extent.height()
        xmax = xmin + 0.5 * self.extent.width()
        ymax = ymin + 0.5 * self.extent.height()
        rect = QgsRectangle(xmin, ymin, xmax, ymax)
        node = QuadNode(self, rect, 2 * y + x, self.depth + 1)
        self.subNodes.append(node)
        if rect.contains(point):
          node.subdivideRecursively(point, maxDepth)

  def listTopQuads(self, quadlist):
    if len(self.subNodes):
      for node in self.subNodes:
        node.listTopQuads(quadlist)
    else:
      quadlist.append(self)
    return quadlist

  def quadByPosition(self, point):
    if not self.extent.contains(point):
      return None
    if len(self.subNodes) == 0:
      return self
    x = min(1, int(2 * (point.x() - self.extent.xMinimum()) / self.extent.width()))
    y = min(1, int(2 * (self.extent.yMaximum() - point.y()) / self.extent.height()))
    return self.subNodes[2 * y + x].quadByPosition(point)

class QuadTree:
  UP = 0
  LEFT = 1
  RIGHT = 2
  DOWN = 3

  def __init__(self, extent=None, point=None, depth=0):
    self.extent = extent
    self.root = QuadNode(self, self.extent, 0)
    if depth > 0:
      self.buildTree(point, depth)

  def setExtent(self, extent):
    self.extent = extent

  def buildTree(self, point, depth):
    if not point or not self.extent.contains(point):
      return
    self.depth = depth
    self.root.subdivideRecursively(point, depth)

  def quads(self):
    return self.root.listTopQuads([])

  def quadByPosition(self, point):
    if not point or not self.extent.contains(point):
      return None
    return self.root.quadByPosition(point)

  def neighbors(self, quad):
    # if neighbor count of one direction is not only one, returns one of neighbors. so totally returns 4 neighbors.
    quads = [None] * 4
    if len(quad.parent.subNodes) == 0:
      return quads
    extent = quad.extent
    center = extent.center()
    m = 0.5 ** self.depth
    quads[self.UP] = self.quadByPosition(QgsPoint(center.x(), extent.yMaximum() + m * extent.height()))
    quads[self.LEFT] = self.quadByPosition(QgsPoint(extent.xMinimum() - m * extent.width(), center.y()))
    quads[self.RIGHT] = self.quadByPosition(QgsPoint(extent.xMaximum() + m * extent.width(), center.y()))
    quads[self.DOWN] = self.quadByPosition(QgsPoint(center.x(), extent.yMinimum() - m * extent.height()))
    return quads
