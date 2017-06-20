package com.gooddata.fixture;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileOutputStream;
import java.io.FileReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.Enumeration;
import java.util.Optional;
import java.util.jar.JarEntry;
import java.util.jar.JarFile;
import java.util.stream.Collectors;

import org.apache.maven.model.Dependency;
import org.apache.maven.model.Model;
import org.apache.maven.model.io.xpp3.MavenXpp3Reader;
import org.codehaus.plexus.util.xml.pull.XmlPullParserException;

public class ResourceManagement {

    private JarFile artifact;

    public ResourceManagement() {
        this.artifact = getArtifact();
    }

    public String getResourceAsString(String path) throws IOException {
        InputStream is = artifact.getInputStream(artifact.getEntry(path));
        return new BufferedReader(new InputStreamReader(is)).lines().collect(Collectors.joining("\n"));
    }

    public void copyResources(ResourceTemplate template, String desDir) throws IOException {
        copyResources(template.getPath(), desDir);
    }

    public void copyResources(String resourcesDir, String desDir) throws IOException {
        Enumeration<JarEntry> entries = artifact.entries();
        while (entries.hasMoreElements()) {
            JarEntry entry = entries.nextElement();
            if (entry.getName().startsWith(resourcesDir)) {
                if (!entry.isDirectory()) {
                    extractResourceToFile(entry, desDir);
                }
            }
        }
    }

    private void extractResourceToFile(JarEntry resource, String desDir) throws IOException {
        File file = new File(desDir, resource.getName());
        if (!file.getParentFile().exists()) {
            file.getParentFile().mkdirs();
        }

        try (InputStream is = artifact.getInputStream(resource);
                FileOutputStream os = new FileOutputStream(file)) {
            while (is.available() > 0) {
                os.write(is.read());
            }
        }
    }

    private String getArtifactVersion() {
        try {
            MavenXpp3Reader reader = new MavenXpp3Reader();
            Model model = reader.read(new FileReader("pom.xml"));
            Optional<Dependency> dependency;

            while (!(dependency = model.getDependencies()
                        .stream()
                        .filter(d -> "gdc-fixture".equals(d.getArtifactId()))
                        .findFirst())
                    .isPresent()) {
                model = reader.read(new FileReader("../pom.xml"));
            }
            return dependency.get().getVersion();

        } catch (IOException e) {
            throw new RuntimeException("Missing pom.xml!");
        } catch (XmlPullParserException e) {
            throw new RuntimeException("There has an error when parsing pom.xml!");
        }
    }

    private JarFile getArtifact() {
        String jarName = "gdc-fixture-" + getArtifactVersion() + ".jar";

        try {
            File artifact = Files.walk(Paths.get(System.getProperty("user.home") + "/.m2/repository"))
                    .map(p -> p.toFile())
                    .filter(f -> f.getName().equals(jarName))
                    .findFirst()
                    .get();
            return new JarFile(artifact);

        } catch (IOException e) {
            throw new RuntimeException(jarName + " not found!");
        }
    }

    public enum ResourceTemplate {
        GOODFIX("fixtures/GoodFix"),
        GOODSALES("fixtures/GoodSales"),
        SINGLE_INVOICE("fixtures/SingleInvoice");

        private String path;

        private ResourceTemplate(String path) {
            this.path = path;
        }

        public String getPath() {
            return path;
        }
    }
}
