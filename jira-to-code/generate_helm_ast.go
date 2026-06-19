package main

import (
	"encoding/json"
	"fmt"
	"go/ast"
	"go/parser"
	"go/token"
	"os"
	"path/filepath"
	"strings"
)

type FileAST struct {
	Path      string          `json:"path"`
	Package   string          `json:"package"`
	Imports   []string        `json:"imports"`
	Types     []TypeInfo      `json:"types"`
	Functions []FunctionInfo  `json:"functions"`
	Variables []VariableInfo  `json:"variables"`
	Constants []ConstantInfo  `json:"constants"`
}

type TypeInfo struct {
	Name    string   `json:"name"`
	Kind    string   `json:"kind"` // struct, interface, alias
	Fields  []Field  `json:"fields,omitempty"`
	Methods []string `json:"methods,omitempty"`
	Doc     string   `json:"doc,omitempty"`
}

type Field struct {
	Name string `json:"name"`
	Type string `json:"type"`
	Tag  string `json:"tag,omitempty"`
}

type FunctionInfo struct {
	Name       string   `json:"name"`
	Receiver   string   `json:"receiver,omitempty"`
	Parameters []Param  `json:"parameters"`
	Returns    []string `json:"returns"`
	Doc        string   `json:"doc,omitempty"`
}

type Param struct {
	Name string `json:"name"`
	Type string `json:"type"`
}

type VariableInfo struct {
	Name string `json:"name"`
	Type string `json:"type"`
	Doc  string `json:"doc,omitempty"`
}

type ConstantInfo struct {
	Name  string `json:"name"`
	Type  string `json:"type"`
	Value string `json:"value,omitempty"`
	Doc   string `json:"doc,omitempty"`
}

func main() {
	// Check if directory is provided as argument, otherwise use default
	helmDir := "pkg/helm"
	if len(os.Args) > 1 {
		helmDir = os.Args[1]
	}

	// Check if directory exists
	if _, err := os.Stat(helmDir); os.IsNotExist(err) {
		// If pkg/helm doesn't exist, try ../console/pkg/helm (for when run from helm-ai-workflows)
		altDir := "../console/pkg/helm"
		if _, err := os.Stat(altDir); err == nil {
			helmDir = altDir
		} else {
			fmt.Fprintf(os.Stderr, "Warning: Directory %s not found. Trying console repo path...\n", helmDir)
			helmDir = "/Users/slakshmi/base/console/pkg/helm"
		}
	}

	var allFiles []FileAST

	err := filepath.Walk(helmDir, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		if !info.IsDir() && strings.HasSuffix(path, ".go") && !strings.HasSuffix(path, "_test.go") {
			fileAST, err := parseFile(path)
			if err != nil {
				fmt.Fprintf(os.Stderr, "Error parsing %s: %v\n", path, err)
				return nil // Continue processing other files
			}
			allFiles = append(allFiles, fileAST)
		}
		return nil
	})

	if err != nil {
		fmt.Fprintf(os.Stderr, "Error walking directory: %v\n", err)
		os.Exit(1)
	}

	output, err := json.MarshalIndent(allFiles, "", "  ")
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error marshaling JSON: %v\n", err)
		os.Exit(1)
	}

	fmt.Println(string(output))
}

func parseFile(path string) (FileAST, error) {
	fset := token.NewFileSet()
	node, err := parser.ParseFile(fset, path, nil, parser.ParseComments)
	if err != nil {
		return FileAST{}, err
	}

	fileAST := FileAST{
		Path:    path,
		Package: node.Name.Name,
	}

	// Extract imports
	for _, imp := range node.Imports {
		importPath := strings.Trim(imp.Path.Value, `"`)
		fileAST.Imports = append(fileAST.Imports, importPath)
	}

	// Extract declarations
	for _, decl := range node.Decls {
		switch d := decl.(type) {
		case *ast.GenDecl:
			processGenDecl(d, &fileAST)
		case *ast.FuncDecl:
			processFuncDecl(d, &fileAST)
		}
	}

	return fileAST, nil
}

func processGenDecl(decl *ast.GenDecl, fileAST *FileAST) {
	doc := strings.TrimSpace(decl.Doc.Text())

	for _, spec := range decl.Specs {
		switch s := spec.(type) {
		case *ast.TypeSpec:
			typeInfo := TypeInfo{
				Name: s.Name.Name,
				Doc:  doc,
			}

			switch t := s.Type.(type) {
			case *ast.StructType:
				typeInfo.Kind = "struct"
				if t.Fields != nil {
					for _, field := range t.Fields.List {
						fieldType := exprToString(field.Type)
						tag := ""
						if field.Tag != nil {
							tag = strings.Trim(field.Tag.Value, "`")
						}

						if len(field.Names) > 0 {
							for _, name := range field.Names {
								typeInfo.Fields = append(typeInfo.Fields, Field{
									Name: name.Name,
									Type: fieldType,
									Tag:  tag,
								})
							}
						} else {
							// Embedded field
							typeInfo.Fields = append(typeInfo.Fields, Field{
								Name: "",
								Type: fieldType,
								Tag:  tag,
							})
						}
					}
				}
			case *ast.InterfaceType:
				typeInfo.Kind = "interface"
				if t.Methods != nil {
					for _, method := range t.Methods.List {
						if len(method.Names) > 0 {
							typeInfo.Methods = append(typeInfo.Methods, method.Names[0].Name)
						}
					}
				}
			default:
				typeInfo.Kind = "alias"
				typeInfo.Fields = []Field{{Type: exprToString(t)}}
			}

			fileAST.Types = append(fileAST.Types, typeInfo)

		case *ast.ValueSpec:
			varType := ""
			if s.Type != nil {
				varType = exprToString(s.Type)
			}

			for i, name := range s.Names {
				if decl.Tok == token.CONST {
					constInfo := ConstantInfo{
						Name: name.Name,
						Type: varType,
						Doc:  doc,
					}
					if i < len(s.Values) {
						constInfo.Value = exprToString(s.Values[i])
					}
					fileAST.Constants = append(fileAST.Constants, constInfo)
				} else {
					fileAST.Variables = append(fileAST.Variables, VariableInfo{
						Name: name.Name,
						Type: varType,
						Doc:  doc,
					})
				}
			}
		}
	}
}

func processFuncDecl(decl *ast.FuncDecl, fileAST *FileAST) {
	funcInfo := FunctionInfo{
		Name: decl.Name.Name,
		Doc:  strings.TrimSpace(decl.Doc.Text()),
	}

	// Extract receiver
	if decl.Recv != nil && len(decl.Recv.List) > 0 {
		funcInfo.Receiver = exprToString(decl.Recv.List[0].Type)
	}

	// Extract parameters
	if decl.Type.Params != nil {
		for _, param := range decl.Type.Params.List {
			paramType := exprToString(param.Type)
			if len(param.Names) > 0 {
				for _, name := range param.Names {
					funcInfo.Parameters = append(funcInfo.Parameters, Param{
						Name: name.Name,
						Type: paramType,
					})
				}
			} else {
				funcInfo.Parameters = append(funcInfo.Parameters, Param{
					Type: paramType,
				})
			}
		}
	}

	// Extract return types
	if decl.Type.Results != nil {
		for _, result := range decl.Type.Results.List {
			funcInfo.Returns = append(funcInfo.Returns, exprToString(result.Type))
		}
	}

	fileAST.Functions = append(fileAST.Functions, funcInfo)
}

func exprToString(expr ast.Expr) string {
	if expr == nil {
		return ""
	}

	switch e := expr.(type) {
	case *ast.Ident:
		return e.Name
	case *ast.SelectorExpr:
		return exprToString(e.X) + "." + e.Sel.Name
	case *ast.StarExpr:
		return "*" + exprToString(e.X)
	case *ast.ArrayType:
		return "[]" + exprToString(e.Elt)
	case *ast.MapType:
		return "map[" + exprToString(e.Key) + "]" + exprToString(e.Value)
	case *ast.InterfaceType:
		return "interface{}"
	case *ast.FuncType:
		return "func"
	case *ast.ChanType:
		return "chan " + exprToString(e.Value)
	case *ast.Ellipsis:
		return "..." + exprToString(e.Elt)
	case *ast.StructType:
		return "struct{}"
	default:
		return fmt.Sprintf("%T", expr)
	}
}
